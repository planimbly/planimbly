export default {
    delimiters: ["[[", "]]"],

    props: {
      year: Number,
      month: Number, //1-12
      attach_days_employees_report: Boolean,
      schedule_for_each_workplace: Array,
      workdays_for_each_employee: Object,
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
      }
    },

    computed:{
      /*
      * Function needed for: -displaying colors and indication in both reports,
      * - displaying employee information under schedule reports 
      */
      all_included_employees(){
        
        let included_employees = null;
        if ((this.schedule_for_each_workplace.length > 0) && (this.workdays_for_each_employee != null)) {
          this.schedule_for_each_workplace.forEach(workplace_schedule => {
            if (workplace_schedule.schedule.days != null) {
              console.log(workplace_schedule.schedule.days); // TODO: RETURNS ALL EMPTY ARRAYS
              for (const day of Object.keys(workplace_schedule.schedule.days)) {
                
                if (workplace_schedule.schedule.days[day].length > 0){
                  //console.log(workplace_schedule.schedule.days[day]);
                  for (const employee of Object.keys(workplace_schedule.schedule.days[day].worker)){

                    if (!(workplace_schedule.schedule.days[day].worker[employee].id in included_employees)){
                      included_employees[workplace_schedule.schedule.days[day].worker[employee].id] = {
                        first_name: workplace_schedule.schedule.days[day].worker[employee].first_name,
                        last_name: workplace_schedule.schedule.days[day].worker[employee].last_name,
                        indicator: null,
                        color: get_nonwhite_random_color,
                        job_time_div_160: this.workdays_for_each_employee[workplace_schedule.schedule.days[day].worker[employee].id.toString()].employee_work_hours.toString()+'/160'
                      }
                      
                    }

                  }
                }

              }
            }
          })

          if (included_employees != null){
            // sorting for display and indication purposes
            included_employees = Object.entries(included_employees).sort((a, b) => {
              // polish locale strings
              return a[1].last_name.localeCompare(b[1].last_name, 'pl', { sensitivity: 'base' });
            });
            // add int indicator to included employees
            included_employees.forEach((employee_entry, index) => {
              employee_entry[1].indicator = index + 1;
            });
            console.log('weszki');
          }
          console.log(included_employees);
          return included_employees;
        }
        else return {
          null: {
            first_name: null,
            last_name: null,
            color: null,
            indicator: null,
            job_time_div_160: null
          },
        }
      }
    },

    template: `
    <div class="PN-pdf-container">
      <div class="PN-report-schedule-table-container">
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">&nbsp</div>
          <div class="PN-schedule-column-content">
            N
          </div>
          <div class="PN-schedule-column-content">
            P
          </div>
          <div class="PN-schedule-column-content">
            R
          </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">1</div>
          <div class="PN-schedule-column-content">
           <span class="badge bg-primary">1</span>
          </div>
          <div class="PN-schedule-column-content">
            <span class="badge bg-primary">3</span>
          </div>
          <div class="PN-schedule-column-content">
            <span class="badge bg-primary">V</span>
          </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">2</div>
          <div class="PN-schedule-column-content">
           <span class="badge bg-primary">1</span>
          </div>
          <div class="PN-schedule-column-content">
            <span class="badge bg-primary">3</span>
          </div>
          <div class="PN-schedule-column-content">
            <span class="badge bg-primary">V</span>
          </div>        
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">3</div>
            <div class="PN-schedule-column-content">
            <span class="badge bg-primary">1</span>
          </div>
          <div class="PN-schedule-column-content">
            <span class="badge bg-primary">3</span>
          </div>
          <div class="PN-schedule-column-content">
            <span class="badge bg-primary">V</span>
          </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">4</div>
            <div class="PN-schedule-column-content">
            <span class="badge bg-primary">1</span>
          </div>
          <div class="PN-schedule-column-content">
            <span class="badge bg-primary">3</span>
          </div>
          <div class="PN-schedule-column-content">
            <span class="badge bg-primary">V</span>
          </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">5</div>
            <div class="PN-schedule-column-content">
            <span class="badge bg-primary">1</span>
          </div>
          <div class="PN-schedule-column-content">
            <span class="badge bg-primary">3</span>
          </div>
          <div class="PN-schedule-column-content">
            <span class="badge bg-primary">V</span>
          </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">6</div>
        <div class="PN-schedule-column-content">
        <span class="badge bg-primary">1</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">3</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">V</span>
       </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">7</div>
        <div class="PN-schedule-column-content">
        <span class="badge bg-primary">1</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">3</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">V</span>
       </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">8</div>
        <div class="PN-schedule-column-content">
        <span class="badge bg-primary">1</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">3</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">V</span>
       </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">9</div>
        <div class="PN-schedule-column-content">
        <span class="badge bg-primary">1</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">3</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">V</span>
       </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">10</div>
        <div class="PN-schedule-column-content">
        <span class="badge bg-primary">1</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">3</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">V</span>
       </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">11</div>
        <div class="PN-schedule-column-content">
        <span class="badge bg-primary">1</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">3</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">V</span>
       </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">12</div>
        <div class="PN-schedule-column-content">
        <span class="badge bg-primary">1</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">3</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">V</span>
       </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">13</div>
        <div class="PN-schedule-column-content">
        <span class="badge bg-primary">1</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">3</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">V</span>
       </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">14</div>
        <div class="PN-schedule-column-content">
        <span class="badge bg-primary">1</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">3</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">V</span>
       </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">15</div>
        <div class="PN-schedule-column-content">
        <span class="badge bg-primary">1</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">3</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">V</span>
       </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">16</div>
        <div class="PN-schedule-column-content">
        <span class="badge bg-primary">1</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">3</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">V</span>
       </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">17</div>
        <div class="PN-schedule-column-content">
        <span class="badge bg-primary">1</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">3</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">V</span>
       </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">18</div>
        <div class="PN-schedule-column-content">
        <span class="badge bg-primary">1</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">3</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">V</span>
       </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">19</div>
        <div class="PN-schedule-column-content">
        <span class="badge bg-primary">1</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">3</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">V</span>
       </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">20</div>
        <div class="PN-schedule-column-content">
        <span class="badge bg-primary">1</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">3</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">V</span>
       </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">21</div>
        <div class="PN-schedule-column-content">
        <span class="badge bg-primary">1</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">3</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">V</span>
       </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">22</div>
        <div class="PN-schedule-column-content">
        <span class="badge bg-primary">1</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">3</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">V</span>
       </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">23</div>
        <div class="PN-schedule-column-content">
        <span class="badge bg-primary">1</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">3</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">V</span>
       </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">24</div>
        <div class="PN-schedule-column-content">
        <span class="badge bg-primary">1</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">3</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">V</span>
       </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">25</div>
        <div class="PN-schedule-column-content">
        <span class="badge bg-primary">1</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">3</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">V</span>
       </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">26</div>
        <div class="PN-schedule-column-content">
        <span class="badge bg-primary">1</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">3</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">V</span>
       </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">27</div>
        <div class="PN-schedule-column-content">
        <span class="badge bg-primary">1</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">3</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">V</span>
       </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">28</div>
        <div class="PN-schedule-column-content">
        <span class="badge bg-primary">1</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">3</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">V</span>
       </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">29</div>
        <div class="PN-schedule-column-content">
        <span class="badge bg-primary">1</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">3</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">V</span>
       </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">30</div>
        <div class="PN-schedule-column-content">
        <span class="badge bg-primary">1</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">3</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">V</span>
       </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">31</div>
        <div class="PN-schedule-column-content">
        <span class="badge bg-primary">1</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">3</span>
       </div>
       <div class="PN-schedule-column-content">
         <span class="badge bg-primary">V</span>
       </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">&nbsp</div>
          <div class="PN-schedule-column-content">
          N
          </div>
          <div class="PN-schedule-column-content">
          P
          </div>
          <div class="PN-schedule-column-content">
          R
          </div>
        </div>
      </div>



      <div class="PN-report-schedule-table-container">
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">&nbsp</div>
          <div class="PN-schedule-column-content">
            N
          </div>
          <div class="PN-schedule-column-content">
            P
          </div>
          <div class="PN-schedule-column-content">
            R
          </div>
        </div>
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">1</div>
          <div class="PN-schedule-column-content">
           <span class="badge bg-primary">1</span>
          </div>
          <div class="PN-schedule-column-content">
            <span class="badge bg-primary">3</span>
          </div>
          <div class="PN-schedule-column-content">
            <span class="badge bg-primary">V</span>
          </div>
        </div>
        
        <div class="PN-schedule-column"><div class="PN-schedule-column-label">&nbsp</div>
          <div class="PN-schedule-column-content">
          N
          </div>
          <div class="PN-schedule-column-content">
          P
          </div>
          <div class="PN-schedule-column-content">
          R
          </div>
        </div>
      </div>
      
      <div v-for="empl in all_included_employees">[[empl]]</div>
    </div>
  `
}