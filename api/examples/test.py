#!/usr/bin/env python
from api import NetSchoolAPI
import json

api = NetSchoolAPI("sgo.tomedu.ru")

data = json.load(open("data.json"))

api.login(data["user"], data["pass"], data["school"])

print()
print(f"Student: {api.student_info['name']}")

print()
print("Overdue tasks:")
for task in api.getOverdueTasks():
    
    print(f"{task['subjectName']} - {task['assignmentName']}")

diary = api.getDiary()["weekDays"]

print()
print("Diary:")

for day in diary:

    daydate = day["date"].split("T")[0]
    
    print()
    print(f'{daydate}')

    for lesson in day["lessons"]:

        marks = []

        if "assignments" in lesson:
            
            assignments = lesson["assignments"]
            for assignment in assignments:

                if "mark" in assignment:

                    mark = assignment["mark"]
                    marks.append(str(mark["mark"]))

        name = lesson["subjectName"]

        if name == "Информатика и ИКТ":
            name = "Информатика"
        elif name == "Основы безопасности жизнедеятельности":
            name = "ОБЖ"

        print(f'    {name} [{", ".join(marks)}]')

print()

api.logout()
