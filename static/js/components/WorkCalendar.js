export default {
    delimiters: ["[[", "]]"],
    props: {
      year: Number,
      month: Number, //1-12
      unit_id: Number,
      workplace_id: Number,
      employee_id: Number,
      show_for_workplace: Boolean,
      schedule: Object
    },

    methods:{
      abbreviate_name(firstName, surname){
        if (typeof firstName == "string" && typeof surname == "string") {
          return firstName.charAt(0) + surname.charAt(0);
        } else {
          return 'Error'
        }
      }
    },

    computed:{
      work_month(){
        const weekdays = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];
        var workMonth = [];



        if (this.show_for_workplace && this.schedule) {

          const element = this.schedule;
          

            if(element.unit_id === this.unit_id &&
               element.workplace_id === this.workplace_id){

                if (element.days != null){
                  for (const day of Object.keys(element.days)) {
                    if (new Date(day).getMonth() === this.month - 1 && new Date(day).getFullYear() === this.year) {
                      let currShifts = [];

                      // With Date() constructor, the date is converted to UMT!
                      // for now, it is assumed that shifts are fetched
                      // from api in the right order (time-wise)
                      // sorting in this script, can be implemented after figuring out
                      // how to compare two hrs in string format

                      if (element.days[day] != null) {

                        for (const shift of Object.keys(element.days[day])) {

                          if (currShifts.some(shift_el => shift_el.shift_type_id === element.days[day][shift].shift_type_id)) {

                            //append employee to an existing shift
                            for (const currShift in currShifts) {

                              if (currShifts[currShift].shift_type_id === element.days[day][shift].shift_type_id) {
                                currShifts[currShift].workers.push(element.days[day][shift].worker);
                              }
                            }

                          } else //add new shift for a given day
                          {

                            currShifts.push({
                              id: element.days[day][shift].id,
                              shift_type_id: element.days[day][shift].shift_type_id,
                              time_start: element.days[day][shift].time_start,
                              time_end: element.days[day][shift].time_end,
                              label: element.days[day][shift].time_start.toString().slice(0, 5) + "-" + element.days[day][shift].time_end.toString().slice(0, 5),
                              workers: [
                                element.days[day][shift].worker
                              ]
                            })

                          }

                        }
                      }
                      
                      

                      currShifts.sort(function(shiftA, shiftB){
      
                        var shiftAstart = new Date("1970-01-01 " + shiftA.time_start);
                        var shiftBstart = new Date("1970-01-01 " + shiftB.time_start);
            
                        return shiftAstart - shiftBstart;
                      })
                      
                      

                      workMonth.push({
                        day: new Date(day),
                        day_label: new Date(day).getDate(),
                        weekday: weekdays[new Date(day).getDay()],
                        shifts: currShifts
                      });

                    }
                  }
              }
            }

        }

        else { //show for employee

        }


        workMonth.sort(function(dayA, dayB){
          return dayA.day - dayB.day
        })

        return workMonth
      },

      grid_blank_fillers(){
        //YYYY-MM-DD, sunday = 0
        const firstDay = new Date(this.year, this.month-1, 1); // CONVERTS TO LOCALTIME; DIFFERENCE BETWEEN UMT POSSIBLE!
        const weekDay = firstDay.getDay();
        if (weekDay === 0) {
          return 6;
        }
        else{
          return weekDay - 1;
        }
      }
    },

    template: `
    <div class="calendar-weekday-label">
      <div class="weekday-label-tile"><div class="weekday-label">Mon</div></div>
      <div class="weekday-label-tile"><div class="weekday-label">Tue</div></div>
      <div class="weekday-label-tile"><div class="weekday-label">Wed</div></div>
      <div class="weekday-label-tile"><div class="weekday-label">Thu</div></div>
      <div class="weekday-label-tile"><div class="weekday-label">Fri</div></div>
      <div class="weekday-label-tile"><div class="weekday-label">Sat</div></div>
      <div class="weekday-label-tile"><div class="weekday-label">Sun</div></div>
    </div>

    <div class="calendar-big">
      <div v-for="filler in grid_blank_fillers" class="tile-transparent"></div>
      <div v-for="day in work_month" class="calendar-tile">
        <div class="tile-content">
          <div class="tile-content-title">
             <div class="cal-day-label-holder">[[day.day_label]]</div>
             <div class="weekday-in-tile-lowres">[[day.weekday]]</div>
          </div>
          <div class="shift-tile-container">
            <div v-for="shift in day.shifts" class="shift-tile">
              [[shift.label]]
              <div v-for="worker in shift.workers" class="employee-tile">
                [[abbreviate_name(worker.first_name, worker.last_name)]]
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    `
}