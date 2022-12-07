export default {
    delimiters: ["[[", "]]"],

    props: {
      year: Number,
      month: Number, //1-12
      attach_days_employees_report: Boolean,
      schedule_for_each_workplace: Array,
      workdays_for_each_employee: Object,
      chosen_workplaces: Array,
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
        // TODO
        return '#67c30d';
      },
      
      /* MAIN METHODS */
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
              ((week_day === 6)||(week_day == 0)) ? 1 : 0 // TODO: INCLUDE NATIONAL HOLIDAYS
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
                    time_start: workplace_schedule.days[day][shift].time_start,
                    time_end: workplace_schedule.days[day][shift].time_end,
                    label:  workplace_schedule.days[day][shift].time_start.toString().slice(0, 5) + 
                            "-" + workplace_schedule.days[day][shift].time_end.toString().slice(0, 5)
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
            time_start: null,
            time_end: null
          },]
        ]
      },
    },

    computed:{
      /*
      * Function needed for: -displaying colors and indication in both reports,
      * - displaying employee information under schedule reports 
      */
      all_included_employees(){
        
        let included_employees = {};
        
        if ((this.schedule_for_each_workplace.length > 0) && (this.workdays_for_each_employee != null)) {
          this.schedule_for_each_workplace.forEach(workplace_schedule => /*for (workplace_schedule of this.schedule_for_each_workplace)*/ {
            
            if (workplace_schedule.schedule.days != null) {
              for (const day of Object.keys(workplace_schedule.schedule.days)) {
                
                if (workplace_schedule.schedule.days[day].length > 0){
                  for (const shift of Object.keys(workplace_schedule.schedule.days[day])){
                    const add_info = workplace_schedule.schedule.days[day][shift].worker.id.toString() in this.workdays_for_each_employee ?
                          this.workdays_for_each_employee[workplace_schedule.schedule.days[day][shift].worker.id.toString()].employee_work_hours.toString() :
                          '(inna jednostka)';
                    
                    if (!(workplace_schedule.schedule.days[day][shift].worker.id in included_employees)){
                      included_employees[workplace_schedule.schedule.days[day][shift].worker.id] = {
                        first_name: workplace_schedule.schedule.days[day][shift].worker.first_name,
                        last_name: workplace_schedule.schedule.days[day][shift].worker.last_name,
                        indicator: null,
                        color: this.get_nonwhite_random_color(),
                        additional_info: add_info
                      }
                    }
                  }
                }

              }
            }
          })
          
          if (Object.keys(included_employees).length > 0){
            // sorting for display and indication purposes
            included_employees = Object.entries(included_employees).sort((a, b) => {
              // polish locale strings
              return a[1].last_name.localeCompare(b[1].last_name, 'pl', { sensitivity: 'base' });
            });
            console.log(included_employees);
            console.log('<-->');
            // add int indicator to included employees
            included_employees.forEach((employee_entry, index) => {
              employee_entry[1].indicator = index + 1;
            });
          }
          console.log(included_employees);
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
      <div v-for="workpl_sch in schedule_for_each_workplace">
        [[workpl_sch.schedule.workplace_name]]
        <div class="PN-report-schedule-table-container">
        
          <div class="PN-schedule-column"><div class="PN-schedule-column-label">&nbsp</div>
            <div v-for="shift_type in workplace_included_shiftTypes(workpl_sch.schedule)" class="PN-schedule-column-content">
              <div class="fw-bold">[[shift_type[1].shiftType_name]]</div>  
            </div>
          </div>

          <div v-for="empl_day in sorted_employees_per_day(workpl_sch.schedule.days, workplace_included_shiftTypes(workpl_sch.schedule))" class="PN-schedule-column">
            <div v-if="empl_day[2]==0" class="PN-schedule-column-label">[[ empl_day[0] ]]</div>
            <div v-else class="PN-schedule-column-label" style="background-color: #888888">[[ empl_day[0] ]]</div>

            <div v-for="empl_shift in empl_day[1]" class="PN-schedule-column-content">
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

          <div class="PN-schedule-column"><div class="PN-schedule-column-label">&nbsp</div>
            <div v-for="shift_type in workplace_included_shiftTypes(workpl_sch.schedule)" class="PN-schedule-column-content">
              <div class="fw-bold">[[shift_type[1].shiftType_name]]</div>  
            </div>
          </div>
        </div>
      </div>


      <div style="display: flex; flex-direction: row; flex-wrap: wrap;">
        <div v-for="empl in all_included_employees">
          &nbsp <b>[[empl[1].indicator]]</b>. [[empl[1].first_name]] [[empl[1].last_name]] [[empl[1].additional_info]]
        </div>
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