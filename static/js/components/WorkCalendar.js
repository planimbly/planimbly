export default {
    delimiters: ["[[", "]]"],
    props: {
      year: Number,
      month: Number, //1-12
      unit_id: Number,
      workplace_id: Number,
      employee_id: Number,
      show_for_workplace: Boolean,
      schedule: Object,
      available_workers: Array,
      available_shift_types: Object,
      absences: Array,
    },
    emits: ['call-rest-api'],
    data () {
      return {
        clickedTileDate: new Date("1970-01-01"),
        addEmployeeToExistingShift_ShiftTypeID: null,
        addNewShift_EmployeeID_array: [],
        addNewShift_ShiftTypeID: null,
        updateEmployeeInExistingShift_ShiftID: null,
        updateEmployeeInExistingShift_ShiftTypeID: null,
      }
    },
    
    methods:{

      /* MOUSE HOVER AWAY BEHAVIOUR*/
      scroll_tile_content_up(){
        var tileContents = this.$refs.tileContent;
        
        for (var i = 0; i < tileContents.length; i++) {
          tileContents[i].scrollTo({top: 0, behaviour: 'smooth'});
        }
        
      },

      /* REST API METHOD CALLS */
      api_post(date_python_format, employee_id, shift_type_id, workplace_id){
        this.$emit('call-rest-api', 'post', null, employee_id, shift_type_id, workplace_id, date_python_format);
      },
      api_put(specific_shift_id, employee_id){
        this.$emit('call-rest-api', 'put', specific_shift_id, employee_id, null, null, null);
      },
      api_delete(specific_shift_id){
        this.$emit('call-rest-api', 'delete', specific_shift_id, null, null, null, null);
      },
      

      /* USER ACTIONS */
      delete_existing_shift(shift_type_id){
        const specific_shift_id_array = [];
        for (const shift of Object.keys(this.clickedTileDay.shifts)) {
          if (this.clickedTileDay.shifts[shift].shift_type_id === shift_type_id) {
              for (const spec_shift_worker in this.clickedTileDay.shifts[shift].workers){
                specific_shift_id_array.push(this.clickedTileDay.shifts[shift].workers[spec_shift_worker].shift_id);
              }
          }
        }
        while (specific_shift_id_array.length > 0){
          this.api_delete(specific_shift_id_array.pop());
        }
      },
      warning_delete_shift(shift_type_id){
        swal({
          title: "Potwierdź usunięcie zmiany",
          icon: "warning",
          buttons: true,
          dangerMode: true,
        })
          .then((willAdd) => {
              if (willAdd) {
                this.delete_existing_shift(shift_type_id)
              }
          });
      },
      delete_all_shifts_in_day(clickedTileDayShifts){
        swal({
          title: "Potwierdź usunięcie zmian z całego dnia",
          icon: "warning",
          buttons: true,
          dangerMode: true,
        })
          .then((willAdd) => {
              if (willAdd) {
                for (let shift of clickedTileDayShifts){
                  this.delete_existing_shift(shift.shift_type_id)
                }
              }
          });
      },
      delete_employee_from_shift(specific_shift_id){
        swal({
          title: "Potwierdź usunięcie pracownika ze zmiany",
          icon: "warning",
          buttons: true,
          dangerMode: true,
        })
          .then((willAdd) => {
              if (willAdd) {
                this.api_delete(specific_shift_id);
              }
        });
      },

      update_employee_for_existing_shift(employee_id){
        if (this.employee_exists_in_worktype(employee_id, this.updateEmployeeInExistingShift_ShiftTypeID)){
          return;
        }
        this.api_put(this.updateEmployeeInExistingShift_ShiftID, employee_id);
      },

      add_new_employee_for_existing_shift(employee_id){
        if (this.employee_exists_in_worktype(employee_id, this.addEmployeeToExistingShift_ShiftTypeID)){
          return;
        }
        this.api_post(
          this.js_date_to_python_format(this.clickedTileDate), 
          employee_id, 
          this.addEmployeeToExistingShift_ShiftTypeID,
          this.workplace_id);
      },

      add_new_shift_type(){
        while (this.addNewShift_EmployeeID_array.length > 0) {
          let employee = this.addNewShift_EmployeeID_array.pop();
          if (!this.employee_exists_in_worktype(employee, this.addNewShift_ShiftTypeID)){
            this.api_post(
              this.js_date_to_python_format(this.clickedTileDate),
              employee,
              this.addNewShift_ShiftTypeID,
              this.workplace_id
            );
          }
        }
        this.nullify_NewShift;
      },

      /* HELPER METHODS */
      js_date_to_python_format(jsdate){
        return new Date(jsdate.getTime() - (jsdate.getTimezoneOffset() * 60000 )).toISOString().split("T")[0];
      },

      employee_exists_in_worktype(employee_id, worktype){
        for (const shift of Object.keys(this.clickedTileDay.shifts)){

          if (this.clickedTileDay.shifts[shift].shift_type_id === worktype) {

            for (const employee of Object.keys(this.clickedTileDay.shifts[shift].workers)){
              if (this.clickedTileDay.shifts[shift].workers[employee].worker.id === employee_id) {
                  console.log('Error message: \nthe employee already exists in current shift type!')
                  return true;
              }
            }
          }
        } 
        return false;
      },

      delete_from_array_NewShiftEmployeesID(id){
        this.addNewShift_EmployeeID_array = this.addNewShift_EmployeeID_array.filter(number => number !== id);
      },

      append_to_array_NewShiftEmployeesID(id){
        this.addNewShift_EmployeeID_array.push(id);
      },

      is_id_in_array_NewShiftEmployeesID(id){
        if (this.addNewShift_EmployeeID_array.includes(id)) {
          return true;
        } else {
          return false;
        }
        
      },

      nullify_NewShift(){
        this.addNewShift_ShiftTypeID = null;
        this.addNewShift_EmployeeID_array = [];
      },

      is_shift_type_already_in_use(id){
        for (const shift of Object.keys(this.clickedTileDay.shifts)) {
          if (this.clickedTileDay.shifts[shift].shift_type_id === id){
            return true;
          }
        }
        return false;
      },

      set_new_tile_date(day){
        this.clickedTileDate = day.day;
      },

      get_absent_employees(date){
        return this.absences.filter(absence => {
          return (new Date(absence.start) <= date) && (date <= new Date(absence.end))
        });
      }
      
    },

    computed:{
      available_workers_filtered(){
        //y.filter(number => number !== id);
        // GET EMPLOYEES, WHO ARE NOT ABSENT AND ARE INCLUDED IN GIVEN WORKPLACE
        if (this.available_workers !== null){
          let present_employees_included_in_workplace = this.available_workers.filter(worker => {
            return !this.get_absent_employees(this.clickedTileDay.day).find(abs_emp => abs_emp.employee === worker.id) &&
                    worker.user_workplace.find(workplace => workplace.id === this.workplace_id)
                  
          }).sort(function(workerA, workerB){
            return workerA.order_number - workerB.order_number
          });
          
          for (const empl of present_employees_included_in_workplace) {
            empl['filtered_type'] = 'present_in_workplace'; 
          }

          let present_employees_included_in_unit = this.available_workers.filter(worker => {
            return !this.get_absent_employees(this.clickedTileDay.day).find(abs_emp => abs_emp.employee === worker.id) &&
                    !worker.user_workplace.find(workplace => workplace.id === this.workplace_id) &&
                    worker.user_unit.find(unit => unit.id === this.unit_id);
                  
          }).sort(function(workerA, workerB){
            return workerA.order_number - workerB.order_number
          }); 

          for (const empl of present_employees_included_in_unit) {
            empl['filtered_type'] = 'present_in_unit'; 
          }

          let present_employees_not_included_in_unit = this.available_workers.filter(worker => {
            return !this.get_absent_employees(this.clickedTileDay.day).find(abs_emp => abs_emp.employee === worker.id) &&
                    !worker.user_workplace.find(workplace => workplace.id === this.workplace_id) &&
                    !worker.user_unit.find(unit => unit.id === this.unit_id);
                  
          }).sort(function(workerA, workerB){
            return workerA.order_number - workerB.order_number
          }); 

          for (const empl of present_employees_not_included_in_unit) {
            empl['filtered_type'] = 'present_other_unit'; 
          }
          
          let absent_employees = this.available_workers.filter(worker => {
            return this.get_absent_employees(this.clickedTileDay.day).find(abs_emp => abs_emp.employee === worker.id);
                      
          }).sort(function(workerA, workerB){
            return workerA.order_number - workerB.order_number
          }); 

          for (const empl of absent_employees) {
            empl['filtered_type'] = 'absent'; 
          }
          
          return present_employees_included_in_workplace.concat(
            present_employees_included_in_unit, 
            present_employees_not_included_in_unit, 
            absent_employees);
        }
        return [];
      },

      available_shift_types_filtered(){

      },

      work_month(){
        const weekdays = ["Niedziela","Poniedziałek","Wtorek","Środa","Czwartek","Piątek","Sobota"];
        var workMonth = [];

        if (this.show_for_workplace && this.schedule) {

          const element = this.schedule;
          

            if(element.unit_id === this.unit_id &&
               element.workplace_id === this.workplace_id){

                if (element.days != null){
                  for (const day of Object.keys(element.days)) {
                    if (new Date(day + 'T01:00').getMonth() === this.month - 1 && new Date(day + 'T01:00').getFullYear() === this.year) {
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
                                currShifts[currShift].workers.push({shift_id: element.days[day][shift].id, worker: element.days[day][shift].worker});
                              }
                            }

                          } else //add new shift for a given day
                          {

                            currShifts.push({
                              //id: element.days[day][shift].id,
                              shift_type_id: element.days[day][shift].shift_type_id,
                              time_start: element.days[day][shift].time_start,
                              time_end: element.days[day][shift].time_end,
                              label: element.days[day][shift].time_start.toString().slice(0, 5) + "-" + element.days[day][shift].time_end.toString().slice(0, 5),
                              workers: [
                                {shift_id: element.days[day][shift].id, worker: element.days[day][shift].worker}
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
                        day: new Date(day + 'T01:00'),
                        day_label: new Date(day + 'T01:00').getDate(),
                        weekday: weekdays[new Date(day + 'T01:00').getDay()],
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
      },

      clickedTileDay(){
        for (const workday of Object.keys(this.work_month)) {
          if (this.work_month[workday].day.toLocaleDateString() === this.clickedTileDate.toLocaleDateString()){
            return this.work_month[workday];
          }
        }  
        return {
          day: this.clickedTileDate,
          day_label: null,
          weekday: null,
          shifts: [
            {
              shift_type_id: null,
              time_start: null,
              time_end: null,
              label: null,
              workers: [
                {shift_id: null, worker: {id: null, first_name: null, last_name: null}}
              ],
            }
          ]
        };
      }
      
    },

    template: `
    <div class="calendar-weekday-label">
      <div class="weekday-label-tile"><div class="weekday-label">Pon</div></div>
      <div class="weekday-label-tile"><div class="weekday-label">Wt</div></div>
      <div class="weekday-label-tile"><div class="weekday-label">Śr</div></div>
      <div class="weekday-label-tile"><div class="weekday-label">Czw</div></div>
      <div class="weekday-label-tile"><div class="weekday-label">Pt</div></div>
      <div class="weekday-label-tile"><div class="weekday-label">Sb</div></div>
      <div class="weekday-label-tile"><div class="weekday-label">Nd</div></div>
    </div>

    <div class="calendar-big">
      <div v-for="filler in grid_blank_fillers" class="tile-transparent"></div>
      <div v-for="day in work_month" class="calendar-tile">
        <div @click="clickedTileDate = day.day" @mouseleave="scroll_tile_content_up" class="tile-content"  data-bs-toggle="modal" data-bs-target="#changeDayScheduleModal" ref="tileContent" style="cursor: pointer">
          <div class="tile-content-title">
             <div class="cal-day-label-holder">[[day.day_label]]</div>
             <div class="weekday-in-tile-lowres">[[day.weekday]]</div>
          </div>
          <div class="shift-tile-container">
            <div v-for="shift in day.shifts" class="shift-tile">
              <div>
                <span class="badge bg-light text-dark ms-1 fw-bold">[[shift.label]]</span>
              </div>
              <div v-for="employee in shift.workers" class="employee-tile d-inline-flex">
                <span class="badge bg-secondary ms-1">[[employee.worker.first_name.toString().slice(0, 1)]]. [[employee.worker.last_name]]</span>           
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="modal fade" id="changeDayScheduleModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                      <h5 class="modal-title" id="changeDayScheduleLabel">[[ this.clickedTileDay.day.toLocaleDateString() ]]</h5>
                      <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                  <ul v-for="shift in clickedTileDay.shifts" class="list-group">
                      <li class="list-group-item mb-2">
                        <div class="container mb-1">
                          <div class="row">
                            <div class="fw-bold col">[[shift.label]] </div>
                            <button @click="addEmployeeToExistingShift_ShiftTypeID = shift.shift_type_id" type="button" 
                            data-bs-target="#pickEmployeeAddToExistingModal" data-bs-toggle="modal" data-bs-dismiss="modal" class="material-icons col-auto" style="border: none; background-color: rgba(0, 0, 255, 0); color: cornflowerblue;">person_add</button>
                            <button @click="warning_delete_shift(shift.shift_type_id)" type="button" class="material-icons col-auto" style="margin-right: 10px; border: none; background-color: rgba(0, 0, 255, 0); color: rgb(255, 90, 90);">delete_outline</button>
                          </div>
                        </div>
                        <ul class="list-group"> 
                                                
                        <li v-for="worker_shift in shift.workers" class="list-group-item list-group-item-action d-inline-flex justify-content-between" style="cursor: pointer">
                            <div @click="updateEmployeeInExistingShift_ShiftID = worker_shift.shift_id; updateEmployeeInExistingShift_ShiftTypeID = shift.shift_type_id"
                              data-bs-target="#pickEmployeeForUpdateModal" data-bs-toggle="modal" data-bs-dismiss="modal">
                                <div class="me-2">[[worker_shift.worker.first_name]] [[worker_shift.worker.last_name]]</div>
                            </div>
                            <button @click="delete_employee_from_shift(worker_shift.shift_id)" type="button" class="material-icons" style="border: none; background-color: rgba(0, 0, 255, 0); color: rgb(255, 90, 90);">delete_outline</button>
                        </li>
                        </ul>
                      </li>
                  </ul> 
                 <button @click="nullify_NewShift" type="button" data-bs-target="#addNewShiftTypeModal"
                  data-bs-toggle="modal" data-bs-dismiss="modal" class="btn btn-primary" style="margin-right: 10px; margin-bottom: 10px">Dodaj zmianę</button> 
                  
                 <button @click="delete_all_shifts_in_day(clickedTileDay.shifts)" type="button" data-bs-dismiss="modal" class="btn btn-outline-danger" style="margin-bottom: 10px">Usuń cały dzień</button>   
                </div>
                
            </div>
        </div>
    </div>
    
    <div class="modal fade" id="pickEmployeeForUpdateModal" tabindex="-1">
        <div class="modal-dialog modal-dialog-scrollable">
            <div class="modal-content">
                <div class="modal-header">
                      <h5 class="modal-title" id="pickEmployeeForUpdateLabel">Wybierz pracownika</h5>
                      <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                      <div class="list-group">
                            <template v-for="worker in available_workers_filtered">
                              <div  @click="update_employee_for_existing_shift(worker.id)" v-if="worker.filtered_type !== 'absent'"
                              class="list-group-item list-group-item-action" data-bs-target="#changeDayScheduleModal" data-bs-toggle="modal" data-bs-dismiss="modal" style="cursor: pointer">
                                  <div class="fw-bold">[[worker.first_name]] [[worker.last_name]]</div> [[worker.username]] 
                                  <div v-if="worker.filtered_type === 'present_other_unit'"><span class="badge bg-danger">Nie należy do tej jednostki</span></div>
                                  <div v-else-if="worker.filtered_type === 'present_in_unit'"><span class="badge bg-warning text-dark">Nie należy do tego działu</span></div>
                              </div>
                              <div v-else 
                              class="list-group-item list-group-item-action disabled" style="cursor: pointer; background-color: rgb(244, 244, 244);">
                                <div class="fw-bold">[[worker.first_name]] [[worker.last_name]]</div> [[worker.username]] <div><span class="badge bg-dark">Nieobecny</span></div>
                              </div> 
                          </template> 
                      </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="modal fade" id="pickEmployeeAddToExistingModal" tabindex="-1">  
        <div class="modal-dialog modal-dialog-scrollable">
            <div class="modal-content">
                <div class="modal-header">
                      <h5 class="modal-title" id="pickEmployeeAddToExistingLabel">Wybierz pracownika</h5>
                      <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                      <div class="list-group">
                          <template v-for="worker in available_workers_filtered">
                            <div  @click="add_new_employee_for_existing_shift(worker.id)" v-if="worker.filtered_type !== 'absent'"
                            class="list-group-item list-group-item-action" data-bs-target="#changeDayScheduleModal" data-bs-toggle="modal" data-bs-dismiss="modal" style="cursor: pointer">
                                <div class="fw-bold">[[worker.first_name]] [[worker.last_name]]</div> [[worker.username]] 
                                <div v-if="worker.filtered_type === 'present_other_unit'"><span class="badge bg-danger">Nie należy do tej jednostki</span></div>
                                <div v-else-if="worker.filtered_type === 'present_in_unit'"><span class="badge bg-warning text-dark">Nie należy do tego działu</span></div>
                            </div>
                            <div v-else 
                            class="list-group-item list-group-item-action disabled" style="cursor: pointer; background-color: rgb(244, 244, 244);">
                              <div class="fw-bold">[[worker.first_name]] [[worker.last_name]]</div> [[worker.username]] <div><span class="badge bg-dark">Nieobecny</span></div>
                            </div> 
                          </template>                      
                      </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="modal fade" id="addNewShiftTypeModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                      <h5 class="modal-title" id="addNewShiftTypeLabel">Wybierz zmianę</h5>
                      <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                      <div class="list-group">
                            <div v-for="shift_type in available_shift_types">
                              <div v-if="is_shift_type_already_in_use(shift_type.id)" class="list-group-item list-group-item-action disabled" style="cursor: pointer">
                                  <div class="fw-bold">[[shift_type.name]] </div>  [[shift_type.hour_start]] - [[shift_type.hour_end]]
                              </div>  
                              <div v-else @click="addNewShift_ShiftTypeID = shift_type.id" 
                              class="list-group-item list-group-item-action" data-bs-target="#pickEmployeesForNewShiftModal" data-bs-toggle="modal" data-bs-dismiss="modal" style="cursor: pointer">
                                  <div class="fw-bold">[[shift_type.name]] </div>  [[shift_type.hour_start]] - [[shift_type.hour_end]]
                              </div> 
                                
                            </div>                    
                      </div>
                </div>
                <div class="modal-footer">
                  <button type="button" class="btn btn-secondary" data-bs-target="#changeDayScheduleModal" data-bs-toggle="modal" data-bs-dismiss="modal" aria-label="Close">Anuluj</button>
                </div>
            </div>

        </div>
    </div>
    
    <div class="modal fade" id="pickEmployeesForNewShiftModal" tabindex="-1">
        <div class="modal-dialog modal-dialog-scrollable">
            <div class="modal-content">
                <div class="modal-header">
                      <h5 class="modal-title" id="pickEmployeesForNewShiftLabel">Wybierz pracowników</h5>
                      <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="list-group">
                      <div v-for="worker in available_workers_filtered">
                          <div v-if="is_id_in_array_NewShiftEmployeesID(worker.id)" @click="delete_from_array_NewShiftEmployeesID(worker.id)" 
                            class="list-group-item list-group-item-action" style="cursor: pointer; background-color: rgb(228, 228, 228);">
                            <div class="fw-bold">[[worker.first_name]] [[worker.last_name]]</div> [[worker.username]]
                            <div v-if="worker.filtered_type === 'present_other_unit'"><span class="badge bg-danger">Nie należy do tej jednostki</span></div>
                            <div v-else-if="worker.filtered_type === 'present_in_unit'"><span class="badge bg-warning text-dark">Nie należy do tego działu</span></div>
                          </div>
                          <div v-else-if="worker.filtered_type === 'absent'" 
                            class="list-group-item list-group-item-action disabled" style="cursor: pointer; background-color: rgb(244, 244, 244);">
                            <div class="fw-bold">[[worker.first_name]] [[worker.last_name]]</div> [[worker.username]] <div><span class="badge bg-dark">Nieobecny</span></div>
                          </div>
                          <div v-else @click="append_to_array_NewShiftEmployeesID(worker.id)" class = "list-group-item list-group-item-action" style="cursor: pointer">
                            <div class="fw-bold">[[worker.first_name]] [[worker.last_name]]</div> [[worker.username]] 
                            <div v-if="worker.filtered_type === 'present_other_unit'"><span class="badge bg-danger">Nie należy do tej jednostki</span></div>
                            <div v-else-if="worker.filtered_type === 'present_in_unit'"><span class="badge bg-warning text-dark">Nie należy do tego działu</span></div>
                          </div>
                      </div>                       
                    </div>
                </div>
                <div class="modal-footer">
                  <button type="button" class="btn btn-secondary" data-bs-target="#changeDayScheduleModal" data-bs-toggle="modal" data-bs-dismiss="modal" aria-label="Close">Anuluj</button>
                  <button v-if="this.addNewShift_EmployeeID_array.length > 0" @click="add_new_shift_type" type="button" class="btn btn-primary" 
                  data-bs-target="#changeDayScheduleModal" data-bs-toggle="modal" data-bs-dismiss="modal">Dodaj</button>
                  <button v-else type="button" class="btn btn-primary" disabled>Dodaj</button>
                </div>
            </div>
        </div>
    </div>
    `
}