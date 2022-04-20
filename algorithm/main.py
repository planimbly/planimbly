from dummy_data import *


# function for preparing data for the algorithm
def gather_data():
    # receive dummy data form outside file
    dummy_data = return_dummy_data()

    return dummy_data


# schedule making function
def make_schedule(data: data):
    # placeholder code for now

    # sample data
    emp: employee = data.employees[-1]
    st = shift_type(1, Time(8, 30), Time(16, 30), 1, '1111100')

    shifts = []

    # magic algorithm preparing the schedule

    d = Date(2022, 4, 12)

    shifts.append(
        {
            'id': 1,  # shift id
            'id_employee': emp,
            'date': d,
            'shift_type': st.id  # shift_type id
        }
    )

    # sample dictionary prepared for sending over to the server
    schedule = {
        'id': 1,  # schedule id
        'date_start': data.date_start,
        'date_end': data.date_end,
        'shifts': shifts
    }

    return schedule


# function for sending the data to the server
def send_data(schedule: dict):
    pass


def main():
    data = gather_data()
    schedule = make_schedule(data)
    send_data(schedule)


if __name__ == "__main__":
    main()
