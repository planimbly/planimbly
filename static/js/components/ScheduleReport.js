export default {
    delimiters: ["[[", "]]"],

    props: {
      year: Number,
      month: Number, //1-12
      attach_days_employees_report: Boolean,
      attach_statistics_employees_report: Boolean,
      schedule_for_each_workplace: Array,
      workdays_for_each_employee: Object,
      chosen_workplaces: Array,
      margin_top_for_statistics: Number,
    },

    data () {
      return {
        schedules_workplace: [
          {
            unit_id: null,
            workplace_id: null,
            unit_name: null,
            workplace_name: null,
            days: {
              null: [{
                id: null,
                shift_type_id: null,
                shift_type_color: null,
                time_start: null,
                time_end: null,
                name: null,
                worker: {id: null, first_name: null, last_name: null}
              }]
            },
            statistics: {}
          }
        ],

      }
    },

    methods:{
      /* HELPER METHODS */
      get_nonwhite_random_color(){
        // TO BE DEPRECATED
        return '#000000';
      },

      best_text_color(hexColorString){
        // convert hex color to RGB
        let r = parseInt(hexColorString.substr(1, 2), 16);
        let g = parseInt(hexColorString.substr(3, 2), 16);
        let b = parseInt(hexColorString.substr(5, 2), 16);

        let relativeLuminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;

        // if luminance is higher than 128, it's better to use black as text color
        return (relativeLuminance > 128) ? "black" : "white";
      },
      
      /* MAIN METHODS */
      /*
      * Function needed for: -displaying absences/employee in employee report
      */
      is_employee_day_absence(date, employee_id, workdays_for_empl){
        if (Object.keys(workdays_for_empl.employees).length != 0) {
          let checked_date = new Date(date + 'T01:00').getDate();

          for (const absence of Object.keys(workdays_for_empl.employees[employee_id].absences)){
            let absence_startdate = new Date(workdays_for_empl.employees[employee_id].absences[absence].start + 'T01:00').getDate();
            let absence_enddate = new Date(workdays_for_empl.employees[employee_id].absences[absence].end + 'T01:00').getDate();

            if (checked_date >= absence_startdate && checked_date <= absence_enddate){
              return true;
            }
          }

          return false;
        }
      },
      /*
      * Function needed for: -displaying total number of working days/employee in employee report
      */
      get_working_days_employee(employee_id, workdays_for_empl){
        let counter = 0;
        if (Object.keys(workdays_for_empl.employees).length != 0) {
          
          for (const day of Object.keys(workdays_for_empl.employees[employee_id].days)){
            counter += Object.keys(workdays_for_empl.employees[employee_id].days[day]).length > 0 ? 1 : 0;
          }
          
        }
        return counter;
      },
      /*
      * Function needed for: -correct data representation in schedule report
      */
      sorted_employees_per_day(schedule_days, sorted_shiftTypes){
        
        let sorted_employees_per_day_list = [];

        if ((sorted_shiftTypes != null ) && (schedule_days != null)) {
          for (const day of Object.keys(schedule_days)) {
            const week_day = new Date(day + 'T01:00').getDay();

            let sorted_employees_per_day_detail = [
              new Date(day + 'T01:00').getDate(),
              [],
              ( ((week_day === 6)||(week_day == 0)) || (this.workdays_for_each_employee.free_days.includes(day)) ) ? 1 : 0
            ];
            for (const shiftType of sorted_shiftTypes){
              var workers_for_shifttype = [];
              for (const shift of Object.keys(schedule_days[day])){
                var curr_emp_indicator = this.all_included_employees.find(emp => emp[0] == schedule_days[day][shift].worker.id)[1].indicator;
                if ((schedule_days[day][shift].shift_type_id == shiftType[0]) && (!(curr_emp_indicator in workers_for_shifttype))) {
                  workers_for_shifttype.push(curr_emp_indicator);
                }
              }
              sorted_employees_per_day_detail[1].push(workers_for_shifttype);
            }
            sorted_employees_per_day_list.push(sorted_employees_per_day_detail);
            
          }
         return sorted_employees_per_day_list;
        }
        else return [
          [null/*day_int*/,[null /*empl_id*/], {free_day: null},]
        ]
      },
      /*
      * Function needed for: -correct data representation in schedule report
      */
      workplace_included_shiftTypes(workplace_schedule){
        
        let included_shiftTypes = {};

        if ((workplace_schedule != null ) && (workplace_schedule.days != null)) {
          for (const day of Object.keys(workplace_schedule.days)) {
               
            if (workplace_schedule.days[day].length > 0){
              
              for (const shift of Object.keys(workplace_schedule.days[day])){
                
                if (!(workplace_schedule.days[day][shift].shift_type_id in included_shiftTypes)){
                  included_shiftTypes[workplace_schedule.days[day][shift].shift_type_id] = {
                    shiftType_name: workplace_schedule.days[day][shift].name,
                    shiftType_code: workplace_schedule.days[day][shift].shift_code,
                    time_start: workplace_schedule.days[day][shift].time_start,
                    time_end: workplace_schedule.days[day][shift].time_end,
                    label:  workplace_schedule.days[day][shift].time_start.toString().slice(0, 5) + 
                            "-" + workplace_schedule.days[day][shift].time_end.toString().slice(0, 5),
                    shift_type_color: workplace_schedule.days[day][shift].shift_type_color
                  }
                }
              }
            }

          }
          
          if (Object.keys(included_shiftTypes).length > 0){
            // sorting for display purposes
            included_shiftTypes = Object.entries(included_shiftTypes).sort((a, b) => {
              var shiftAstart = new Date("1970-01-01 " + a[1].time_start);
              var shiftBstart = new Date("1970-01-01 " + b[1].time_start);
              
              return shiftBstart - shiftAstart;
            });
            
          } else {
            included_shiftTypes = [];
          }
          
          return included_shiftTypes;
        }
        else return
         [
          [null/*(=shiftType_id)*/, {
            shiftType_name: null,
            shiftType_code: null,
            time_start: null,
            time_end: null,
            shift_type_color: null
          },]
        ]
      },
    },

    computed:{
      jobtime_norm(){
         if (this.schedule_for_each_workplace[0] != undefined) {
            return this.schedule_for_each_workplace[0].schedule.jobtime;
         }
      },
      unit_name(){
        if (this.schedule_for_each_workplace[0] != undefined) {
           return this.schedule_for_each_workplace[0].schedule.unit_name;
        }
     },
      /*
      * Function needed for: -displaying holidays and weekends
      */
      weekends_holidays(){
        let weekends_holidays_arr = [];
        if (Object.keys(this.workdays_for_each_employee.employees).length != 0) {
          
          for (const day of Object.keys(this.workdays_for_each_employee.employees[this.all_included_employees[0][0]].days)){
            const week_day = new Date(day + 'T01:00').getDay();

            if ( ((week_day === 6)||(week_day == 0)) || (this.workdays_for_each_employee.free_days.includes(day)) ){
              weekends_holidays_arr.push(day);
            }
          }
          
        }
        return weekends_holidays_arr;
      },
      /*
      * Function needed for: -displaying colors and indication in both reports,
      * - displaying employee information under schedule reports 
      */
      all_included_employees(){
        
        let included_employees = {};
        
        if ((this.schedule_for_each_workplace.length > 0) && (this.workdays_for_each_employee.employees != null)) {
          this.schedule_for_each_workplace.forEach(workplace_schedule => /*for (workplace_schedule of this.schedule_for_each_workplace)*/ {
            
            if (workplace_schedule.schedule.days != null) {
              for (const day of Object.keys(workplace_schedule.schedule.days)) {
                
                if (workplace_schedule.schedule.days[day].length > 0){
                  for (const shift of Object.keys(workplace_schedule.schedule.days[day])){
                    const add_info = (workplace_schedule.schedule.days[day][shift].worker.id.toString() in this.workdays_for_each_employee.employees) && 
                          (this.workdays_for_each_employee.employees[workplace_schedule.schedule.days[day][shift].worker.id.toString()].employee_work_hours.toString() != "1") ?
                          this.workdays_for_each_employee.employees[workplace_schedule.schedule.days[day][shift].worker.id.toString()].employee_work_hours.toString() : "";
                    
                    if (!(workplace_schedule.schedule.days[day][shift].worker.id in included_employees)){
                      included_employees[workplace_schedule.schedule.days[day][shift].worker.id] = {
                        first_name: workplace_schedule.schedule.days[day][shift].worker.first_name,
                        last_name: workplace_schedule.schedule.days[day][shift].worker.last_name,
                        indicator: workplace_schedule.schedule.days[day][shift].worker.order_number,
                        color: this.get_nonwhite_random_color(), // UNUSED
                        additional_info: add_info
                      }
                    }
                  }
                }

              }
            }
          })
          
          if (Object.keys(included_employees).length > 0){
            // check if you can use order_number as indication (ergo if every participant has an order_number)
            let sort_by_order_number = () => {
              let found_null = false;
              Object.entries(included_employees).forEach((employee_entry) => {
                if (employee_entry[1].indicator === null) { found_null = true; }
              })
              return found_null ? false : true;
            }
            // sorting for display and indication purposes
            if (sort_by_order_number()){
              included_employees = Object.entries(included_employees).sort((a, b) => {
                return a[1].indicator - b[1].indicator;
              });
            } 
            else {
              included_employees = Object.entries(included_employees).sort((a, b) => {
                // polish locale strings
                return a[1].last_name.localeCompare(b[1].last_name, 'pl', { sensitivity: 'base' });
              });
              // add int indicator to included employees
              included_employees.forEach((employee_entry, index) => {
                employee_entry[1].indicator = index + 1;
              });
            }
          }
          return included_employees;
        }
        else return [
          [null, {
            first_name: null,
            last_name: null,
            color: null,
            indicator: null,
            job_time_div_160: null
          },]
        ]
      }
    },

    template: `
    <div class="PN-pdf-container">

      <div class="PN-pdf-subcontainer" id="report_element_to_measure">
        <div class="PN-report-header">
          <div class="PN-report-header-item fw-bold"> Dyżury w [[ unit_name ]]</div>
          <div class="PN-report-header-item"><div class="fw-bold">[[month]].[[year]] </div>&nbsp(norma [[ jobtime_norm ]])</div>
        </div>
        <div v-for="workpl_sch in schedule_for_each_workplace">
          <div class="PN-workplace-title mb-1"> [[workpl_sch.schedule.workplace_name]] </div>
          <div class="PN-report-schedule-table-container">
          
            <div class="PN-schedule-column"><div class="PN-schedule-column-label">&nbsp</div>
              <div v-for="shift_type in workplace_included_shiftTypes(workpl_sch.schedule)" class="PN-schedule-column-content" :style="{ 'background-color': shift_type[1].shift_type_color }">
                <div class="flex-column ms-1 me-1">
                  <div class="fw-bold" :style="{ 'color': best_text_color(shift_type[1].shift_type_color) }" >
                  [[shift_type[1].shiftType_name]]  ( [[ shift_type[1].shiftType_code ]] ) 
                  </div>  
                  <div :style="{ 'color': best_text_color(shift_type[1].shift_type_color) }">[[shift_type[1].label]]</div> 
                </div>
              </div>
            </div>

            <div v-for="empl_day in sorted_employees_per_day(workpl_sch.schedule.days, workplace_included_shiftTypes(workpl_sch.schedule))" class="PN-schedule-column">
              <div v-if="empl_day[2]==0" class="PN-schedule-column-label">[[ empl_day[0] ]]</div>
              <div v-else class="PN-schedule-column-label" style="background-color: #C2C2C2">[[ empl_day[0] ]]</div>
              
              <div v-for="empl_shift in empl_day[1]" class="PN-schedule-column-content" v-if="empl_day[2]==0">
                  <div v-if="empl_shift.length != 0" class="PN-flex-row">
                    <div v-for="empl in empl_shift" class="PN-schedule-column-content-employee">
                        [[empl]]
                    </div>
                  </div>
                  <div v-else class="PN-flew-row">
                    &nbsp
                  </div>                 
              </div>
            
            
              <div v-for="empl_shift in empl_day[1]" class="PN-schedule-column-content" style="background-color: #C2C2C2" v-if="empl_day[2]!=0">
                  <div v-if="empl_shift.length != 0" class="PN-flex-row">
                    <div v-for="empl in empl_shift" class="PN-schedule-column-content-employee"> 
                        [[empl]]
                    </div>
                  </div>
                  <div v-else class="PN-flew-row">
                    &nbsp
                  </div>                 
              </div>
            </div>
          </div>
        </div>

        
        <div v-if="attach_days_employees_report">
          <div class="PN-report-employee-table-container" v-if="workdays_for_each_employee != null && schedule_for_each_workplace[0] != null">
            <div class="PN-day-label-row">
                <div class="PN-day-label-content-start">
                  &nbsp
                </div>
                <div v-for="(value, date) in schedule_for_each_workplace[0].schedule.days">
                  <div v-if="weekends_holidays.includes(date)" class="PN-day-label-content" style="background-color: #C2C2C2">
                    [[new Date(date + 'T01:00').getDate()]]
                  </div>
                  <div v-else class="PN-day-label-content">
                    [[new Date(date + 'T01:00').getDate()]]
                  </div>
                </div>
                <div class="PN-day-counter-content">
                Liczba dni
              </div>
            </div>
            <div v-for="employee_info in all_included_employees" class="PN-employee-row">
              <div class="PN-employee-content-start"> 
                <b>[[employee_info[1].indicator]]</b>. [[employee_info[1].first_name]] [[employee_info[1].last_name]] [[employee_info[1].additional_info]]
              </div>

              <div v-for="(workday, workdate) in workdays_for_each_employee.employees[employee_info[0]].days"> 
                <div class="PN-employee-content" :style="{ 'background-color': weekends_holidays.includes(workdate) ? '#C2C2C2' : 'inherit'}" >
                  <div v-if="is_employee_day_absence(workdate, employee_info[0], workdays_for_each_employee)" class="PN-container-flex-center-div">
                    <div class="material-icons md-14">person_off</div>
                  </div>
                  <div v-else-if="workday.length > 0">
                    [[workday[0].shift_code]]
                  </div>
                  <div v-else>
                    &nbsp
                  </div>
                </div>
              </div>


              <div class="PN-day-counter-content">
                [[get_working_days_employee(employee_info[0], workdays_for_each_employee)]]
              </div>
          
            </div>

          </div>
        </div>

        <div v-else style="display: flex; flex-direction: row; flex-wrap: wrap;">
          <div v-for="empl in all_included_employees">
            &nbsp <b>[[empl[1].indicator]]</b>. [[empl[1].first_name]] [[empl[1].last_name]] [[empl[1].additional_info]]
          </div>
        </div>

      </div>

      <div v-if="attach_statistics_employees_report" :style="{ 'margin-top': margin_top_for_statistics + 'px' }">
        STATISTICS
        [[ margin_top_for_statistics ]]
      </div>

      <!--
      <div v-for="workpl_sch in schedule_for_each_workplace">
        [[workplace_included_shiftTypes(workpl_sch.schedule)]]  
      </div>
      <br>
      <div v-for="workpl_sch in schedule_for_each_workplace">
        [[sorted_employees_per_day(workpl_sch.schedule.days, workplace_included_shiftTypes(workpl_sch.schedule))]]  
      </div>
      <br>
      <br>
      <div v-for="workpl_sch in schedule_for_each_workplace">
        
        <div v-for="(day_props, day) in workpl_sch.schedule.days">
          [[day]] :: [[day_props]]
        </div>
        
      </div>
      -->
    </div>
  `
}