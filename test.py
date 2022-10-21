#!/usr/bin/env python
from nsapi import NetSchoolAPI
import json

api = NetSchoolAPI("sgo.tomedu.ru")

for school in api.getSchoolList():
    if "Стреже" in school["addressString"]:
        print(school)
exit()

data = json.load(open("test_data.json"))

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
    print(f"{daydate}")

    for lesson in day["lessons"]:

        marks = []
        tasks = []

        if "assignments" in lesson:

            assignments = lesson["assignments"]
            for assignment in assignments:

                if "mark" in assignment:

                    mark = assignment["mark"]
                    marks.append(str(mark["mark"]))

                if "assignmentName" in assignment:

                    # Получим id типа домашнего задания
                    typeid = api.getAssignmentTypeId("Домашнее задание")

                    if assignment["typeId"] == typeid:

                        tasks.append(assignment["assignmentName"])

        name = lesson["subjectName"]

        if name == "Информатика и ИКТ":
            name = "Информатика"
        elif name == "Основы безопасности жизнедеятельности":
            name = "ОБЖ"

        print(f'    {name} [{", ".join(marks)}]')

        if tasks != []:

            for task in tasks:
                print(f"        {task}")

print()

api.logout()
