import re
import string
import random
import os
import ayon_api
import shotgun_api3
import getting_flow_data


def generate_random_string(length=32):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def sequence_name(files):
    if not files:
        return None, None, None, None

    files = sorted(files)
    first, last = files[0], files[-1]

    # find frame number in first file
    match = re.search(r'(\d+)(?!.*\d)', first)
    if not match:
        return first, None, None, None  # no digits found

    frame_digits = match.group(1)
    padding = len(frame_digits)

    start, end = match.span(1)

    # %0Xd style (for AYON/pipeline)
    printf_pattern = first[:start] + f"%0{padding}d" + first[end:]

    # #### style (for Nuke)
    hash_pattern = first[:start] + ("#" * padding) + first[end:]

    # Extract first and last frame numbers
    start_frame = int(frame_digits)
    end_frame = int(re.search(r'(\d+)(?!.*\d)', last).group(1))

    return printf_pattern, hash_pattern, start_frame, end_frame


# "//pixdrive/production/projects/SRV_TST/sequences/HFL/SH_005/input/plate/v001/TRA_303_046_010_E01_v01/TRA_303_046_010_E01_v01.1001.exr",
# xcv = "//pixdrive/production/projects/SRV_TST/sequences/HFL/SH_005/input/plate/v001/TRA_303_046_010_E01_v01/TRA_303_046_010_E01_v01.1001.{ext}",
def publish_to_ayon(project_, name_, folder_data_, task_data_, files_data_, template_, frame_start_, frame_end_, path_to_frames):
    # create plate product,
    # create version
    # create representation for each files

    product_ = connection.create_product(project_name=project_, name=name_+"roto_v001",
                                         product_type='plate', folder_id=folder_data_.get('id'))

    print("created a product", product_)
    version_ = connection.create_version(project_name=project_, product_id=product_,
                                         version=1, task_id=task_data_.get('id'),
                                         attrib={"pathToFrames":path_to_frames})
    print(f"created a version {version_}")
    representation_ = connection.create_representation(project_name=project_, version_id=version_,
                                                       name='exr', files=files_data_, attrib={'template': template_,
                                                                                              'frameEnd': frame_end_,
                                                                                              'frameStart': frame_start_,
                                                                                              'description': 'this is client plates'},
                                                       data={
                                                           'context': {'asset': folder_data_.get('name'), 'ext': 'exr',
                                                                       'family': 'plate',
                                                                       'project': {'code': project_, 'name': project_},
                                                                       'representation': 'exr',
                                                                       'folder': {'name': folder_data_.get('name'),
                                                                                  'parents': folder_data_.get(
                                                                                      'parents'),
                                                                                  'hierarchy': folder_data_.get(
                                                                                      'hierarchy'),
                                                                                  'task': {
                                                                                      'name': task_data_.get('name'),
                                                                                      'type': 'Roto'}},
                                                                       'frame': frame_start_

                                                                       }
                                                       })
    print(f"created a representation {representation_}")


sg = shotgun_api3.Shotgun('https://pixstone.shotgunstudio.com', 'pixflow_desktop_tool',
                          'siwrh@bnzzfwpuo8gujuHfkbg', http_proxy='192.168.15.7:3128')

ayon_url = 'http://172.31.6.203:5000'
user_token = ayon_api.login_to_server(url=ayon_url, username='input_user', password='5292684')
connection = ayon_api.ServerAPI(token=user_token, base_url=ayon_url)

project_id = 6356
shot_link_data, raw_data = getting_flow_data.get_the_shot_link_data(sg_connection=sg, project_id=project_id)

injectable_shots = [shot for shot in shot_link_data if
                    shot.get('status') == 'cmpt']  # filtering the shot link page in the data

# identify the path or products the folder
project_name = 'SRV_TST'
project_root = f'//pixdrive/production/projects/{project_name}'  # need to automate this

# getting the shot path from ayon

for inject_shot in injectable_shots:
    shot_folder = connection.get_folder_by_name(project_name=project_name, folder_name=inject_shot.get('name'))
    input_folder = f'{project_root}{shot_folder.get("path")}/input'
    shot_folder_id = shot_folder.get('id')
    publishable_step = inject_shot.get('linkedprocess')
    # filter the task in publishing step and ayon task {roto}--->{roto}
    tasks = [task for task in connection.get_tasks(project_name=project_name, folder_ids=shot_folder_id)
             if task.get('taskType') in publishable_step]

    # going for the plate
    plate_base_folder = f"{input_folder}/plate"
    available_versions = os.listdir(plate_base_folder)
    latest_version = max(available_versions, key=lambda v: int(v[1:]))

    plate_folder = f"{plate_base_folder}/{latest_version}"
    # get the available products inside the plate folder
    available_products = os.listdir(plate_folder)
    for product in available_products:
        exr_files = [x for x in os.listdir(f"{plate_folder}/{product}") if
                     x.endswith('.exr')]  # ignoring other files except .exr
        printf_pattern, template, frame_start, frame_end = sequence_name(exr_files)
        # template_name = f"{plate_folder}/{product}/{exr_files[0]}"
        template_name = f"{plate_folder}/{product}/{template}"
        path_to_frames = f"{plate_folder}/{product}/{printf_pattern}"
        for task in tasks:
            file_data = []
            for exr in exr_files:
                _data_ = {
                    'id': generate_random_string(),
                    'name': exr,
                    'path': f"{plate_folder}/{product}/{exr}"
                }
                file_data.append(_data_)

            task_id = task.get('id')
            publish_to_ayon(project_=project_name, name_=product, folder_data_=shot_folder, task_data_=task,
                            files_data_=file_data, template_=template_name, frame_end_=frame_end,
                            frame_start_=frame_start, path_to_frames=path_to_frames)
