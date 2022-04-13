from algorithm.classes import data, employee, shift_type
from classes import *
from sqlite3 import Date, Time

shift_types = []

pierwsza_zmiana = shift_type(0, Time(6), Time(14), 0, '1111100')
druga_zmiana = shift_type(0, Time(14), Time(22), 0, '1111100')
trzecia_zmiana = shift_type(0, Time(22), Time(6), 0, '1111100')

shift_types.append(pierwsza_zmiana)
shift_types.append(druga_zmiana)
shift_types.append(trzecia_zmiana)

employees = []

employees.append(employee(0, 40))
employees.append(employee(1, 40))
employees.append(employee(2, 40))
employees.append(employee(3, 40))

def return_dummy_data():
    return data(employees, [], Date(2022, 4, 1), Date(2022, 4, 30), shift_types)