# change the task status when workfile is created by user
import time

import ayon_api
from typing import Set, Dict, Any

# login to ayon server via input user
# note : if we no need to change the status in shotgrid we can use service user instead of human user

url = 'http:ayon_website_url'
user_token = ayon_api.login_to_server(url=url, username='user', password='user password')
connection = ayon_api.ServerAPI(base_url=url, token=user_token)


def change_status(evt):
    data = connection.get_event(event_id=evt['id'])
    project_name = data.get('project')
    parent_id = data['summary']['parentId']
    user = data.get('user')
    description = data.get('description')
    try:
        # parent_task = connection.get_folder_by_id(project_name=project_name, folder_id=parent_id)
        parent_task = connection.get_task_by_id(project_name=project_name, task_id=parent_id)
        print(f"current task status -----> {parent_task.get('status')}")
        print(f"current task name ----> {parent_task.get('name')} ---> type {parent_task.get('taskType')} ")
        if parent_task.get('status') == 'Ready to start':
            try:
                print("going to change the status")
                connection.update_task(project_name=project_name, task_id=parent_id, status='In progress')
                print('task change completed')
            except Exception as e:
                print(e)

    except Exception as error:
        print(f"lol error happened {error}")
        parent_task = "lol this is an error"
    # parent_task = connection.get_folder_by_id(project_name=evt.get('project'),
    #                                           folder_id=data.get('summary').get('parentId'))

    print("Event Data : ", data)
    print(f"User : {user}")
    print(f"Project : {project_name}")
    print(f"Parent Id : {parent_id}")
    print(f"description : {description}")
    print(f"Parent Task : {parent_task}")
    print("____________________")


def monitor_workfile_events():
    monitor_events = True
    old_events: Set[str] = set()
    while monitor_events:
        try:
            for evt in connection.get_events(topics='entity.workfile.created'):
                evt_id = evt.get('id')
                if evt_id and evt_id not in old_events:
                    old_events.add(evt_id)
                    change_status(evt)
        except Exception as error:
            print(f"loop stopped here is the error {error}")
        time.sleep(1)


monitor_workfile_events()
# 6cc038fa923411f0b2fbb28d2b833c83
