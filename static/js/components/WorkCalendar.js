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
      available_workers: Object,
      available_shift_types: Object
    },

    data () {
      return {
        clickedTileDay: {
          day: new Date("1970-01-01"),
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
        },
        //addEmployeeToExistingShift_EmployeeID: null,
        addEmployeeToExistingShift_ShiftTypeID: null,
        addNewShift_EmployeeID_array: [],
        addNewShift_ShiftTypeID: null,
        //updateEmployeeInExistingShift_EmployeeID: null,
        updateEmployeeInExistingShift_ShiftID: null,
      }

    },

    methods:{
      abbreviate_name(firstName, surname){
        if (typeof firstName == "string" && typeof surname == "string") {
          return firstName.charAt(0) + surname.charAt(0);
        } else {
          return 'Error'
        }
      },
      print(string){
        console.log(string);
      },

      update_employee_for_existing_shift(employee_id){
        console.log('PUT: '+this.updateEmployeeInExistingShift_ShiftID+' employee: '+employee_id);
      },

      add_new_employee_for_existing_shift(employee_id){
        if (this.employee_exists_in_worktype(employee_id, this.addEmployeeToExistingShift_ShiftTypeID)){
          return;
        }
        console.log('ADD NEW: '+this.addEmployeeToExistingShift_ShiftTypeID+' employee: '+employee_id);
      },

      add_new_shift_type(){
        console.log('ADD NEW SHIFT: '+this.addNewShift_ShiftTypeID+' employees: ');
        console.log(this.addNewShift_EmployeeID_array);
        this.nullify_NewShift;
      },

      employee_exists_in_worktype(employee_id, worktype){
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
      
    },

    computed:{
      available_workers_filtered(){

      },

      available_shift_types_filtered(){

      },

      work_month(){
        const weekdays = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];
        var workMonth = [];

        console.log(this.schedule);
        console.log(this.available_workers);
        console.log(this.available_shift_types);

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
        <div @click="clickedTileDay = day" class="tile-content"  data-bs-toggle="modal" data-bs-target="#changeDayScheduleModal">
          <div class="tile-content-title">
             <div class="cal-day-label-holder">[[day.day_label]]</div>
             <div class="weekday-in-tile-lowres">[[day.weekday]]</div>
          </div>
          <div class="shift-tile-container">
            <div v-for="shift in day.shifts" class="shift-tile">
              [[shift.label]]
              <div v-for="employee in shift.workers" class="employee-tile">
                  [[employee.worker.first_name]] [[employee.worker.last_name]]               
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
                            <button @click="print('usuniecie zmiany')" type="button" class="btn btn-outline-danger btn-sm col col-lg-2">Usuń</button>
                          </div>
                        </div>
                        <ul class="list-group"> 
                            <div class="container">                     
                              <li v-for="worker_shift in shift.workers" class="list-group-item row">
                                  <div @click="updateEmployeeInExistingShift_ShiftID = worker_shift.shift_id" data-bs-target="#pickEmployeeForUpdateModal"
                                   data-bs-toggle="modal" data-bs-dismiss="modal" class="col">
                                      [[worker_shift.shift_id]] [[worker_shift.worker]]
                                  </div>
                                  <button @click="print('usuniecie pracownika')" type="button" class="btn btn-outline-danger btn-sm col col-lg-2">Usuń</button>
                              </li>
                            </div>  
                            <li class="list-group-item"> <button @click="addEmployeeToExistingShift_ShiftTypeID = shift.shift_type_id" type="button" 
                            data-bs-target="#pickEmployeeAddToExistingModal" data-bs-toggle="modal" data-bs-dismiss="modal" class="btn btn-outline-primary btn-sm">
                            Dodaj pracownika
                                </button> 
                            </li>
                        </ul>
                      </li>
                  </ul> 
                 <button @click="nullify_NewShift" type="button" data-bs-target="#addNewShiftTypeModal"
                  data-bs-toggle="modal" data-bs-dismiss="modal" class="btn btn-primary">Dodaj zmianę</button>                   
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
                            <div v-for="worker in available_workers" @click="update_employee_for_existing_shift(worker.id)" 
                            class="list-group-item list-group-item-action" data-bs-target="#changeDayScheduleModal" data-bs-toggle="modal" data-bs-dismiss="modal">
                                <div class="fw-bold">[[worker.first_name]] [[worker.last_name]]</div> [[worker.username]]
                            </div>                       
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
                            <div v-for="worker in available_workers" @click="add_new_employee_for_existing_shift(worker.id)" 
                            class="list-group-item list-group-item-action" data-bs-target="#changeDayScheduleModal" data-bs-toggle="modal" data-bs-dismiss="modal">
                                <div class="fw-bold">[[worker.first_name]] [[worker.last_name]]</div> [[worker.username]] // ADD HERE UNIT NAME AS WELL - DISABLE IF THE EMPLOYEE IS ON HOLIDAYS
                            </div>                       
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
                              <div v-if="is_shift_type_already_in_use(shift_type.id)" class="list-group-item list-group-item-action disabled">
                                  <div class="fw-bold">[[shift_type.name]]: ([[shift_type.id]]) </div>  [[shift_type.hour_start]] - [[shift_type.hour_end]]
                              </div>  
                              <div v-else @click="addNewShift_ShiftTypeID = shift_type.id" 
                              class="list-group-item list-group-item-action" data-bs-target="#pickEmployeesForNewShiftModal" data-bs-toggle="modal" data-bs-dismiss="modal">
                                  <div class="fw-bold">[[shift_type.name]]: ([[shift_type.id]]) </div>  [[shift_type.hour_start]] - [[shift_type.hour_end]]
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
                      <div v-for="worker in available_workers">
                          <div v-if="is_id_in_array_NewShiftEmployeesID(worker.id)" @click="delete_from_array_NewShiftEmployeesID(worker.id)" class="list-group-item list-group-item-action active">
                            <div class="fw-bold">[[worker.first_name]] [[worker.last_name]]</div> [[worker.username]]
                          </div>
                          <div v-else @click="append_to_array_NewShiftEmployeesID(worker.id)" class = "list-group-item list-group-item-action">
                            <div class="fw-bold">[[worker.first_name]] [[worker.last_name]]</div> [[worker.username]]
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