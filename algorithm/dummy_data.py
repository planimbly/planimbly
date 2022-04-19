from multiprocessing import dummy
from algorithm.classes import data, employee, shift_type
from classes import *
from sqlite3 import Date, Time5
import random as rd

def return_dummy_data():
    shift_types = []

    pierwsza_zmiana = shift_type(0, Time(6), Time(14), 0, '1111100')
    druga_zmiana = shift_type(0, Time(14), Time(22), 0, '1111100')
    trzecia_zmiana = shift_type(0, Time(22), Time(6), 0, '1111100')

    shift_types.append(pierwsza_zmiana)
    shift_types.append(druga_zmiana)
    shift_types.append(trzecia_zmiana)

    employees = []

    dummy_shifts = []

    for i in range(1):
        rand_id = rd.randint(0, 65500)
        dummy_shifts.append(shift(rand_id, 3, 0, Date(2022, 0, 1), pierwsza_zmiana))

    dummy_schedule = schedule(0, Date(2022, 4, 1), Date(2022, 4, 30), dummy_shifts)

    employees.append(employee(0, 40))
    employees.append(employee(1, 40))
    employees.append(employee(2, 40))
    employees.append(employee(3, 40))

    return data(employees, [dummy_schedule], Date(2022, 4, 1), Date(2022, 4, 30), shift_types)