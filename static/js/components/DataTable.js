export default {
    delimiters: ["[[", "]]"],

    props: {
        /*
        [{
            title: ...,
            editable: false/true,

         }, 
        ...]
        */
        fields_options: {
            type: Array,
            required: true,
        },
        data_rows: {
            type: Array,
            required: true,
        },
        options: {
            type: Object,
            default: {
                start_mobile_view_px: 1450,
                editable: true,
            },
        }

    },

    data () {
      return {
        mock_field_options: [
            {title: 'Start zmiany', editable: true, property_name: 'hour_start', type: 'time', allow_filter: true, default_filter: 'asc'},
            {title: 'Koniec zmiany', editable: true, property_name: 'hour_end', type: 'time', allow_filter: true},
            {title: 'Nazwa', editable: true, property_name: 'name', type: 'text', highlighted: true, allow_filter: true},
            {title: 'Skrót', editable: true, property_name: 'shift_code', type: 'text', allow_filter: true},
            {title: 'Kolor', editable: true, property_name: 'color', type: 'color'},
            {title: 'Zapotrzebowanie', editable: true, property_name: 'demand', type: 'number', allow_filter: true},
            {title: 'W użyciu', editable: true, property_name: 'is_used', type: 'checkbox', allow_filter: true},
        ],
        mock_data_rows: [
            { "id": 1, "hour_start": "06:00:00", "hour_end": "14:00:00", "name": "M", "shift_code": "AAA", "workplace": 1, "demand": 1, "color": "#BEDAFF", "active_days": "1111111", "is_used": true }, { "id": 2, "hour_start": "14:00:00", "hour_end": "22:00:00", "name": "A", "shift_code": "AAC", "workplace": 1, "demand": 3, "color": "#BEDAFF", "active_days": "1111111", "is_used": true }, { "id": 3, "hour_start": "22:00:00", "hour_end": "06:00:00", "name": "N", "shift_code": "AFA", "workplace": 1, "demand": 1, "color": "#BEDAFF", "active_days": "1111111", "is_used": false } 
        ],
        window_width: 0,
        row_to_edit_mobile: null,
        user_changed_filter_property: null,
        user_changed_filter_is_asc: null,
      }
    },

    methods:{
        resize_handler(e){
            this.window_width = window.innerWidth;
        },
        edit_row_datatable(){
            console.log('edit row');
        },
        set_row_to_edit_mobile(row){
            console.log('row to edit below');
            this.row_to_edit_mobile = Object.assign({}, row);
            console.log(this.row_to_edit_mobile);
        },
        filter_triangle_to_show(field){
            if (this.user_changed_filter_property === null && field.hasOwnProperty('default_filter')){
                return field.default_filter === 'desc' ? 'desc' : 'asc';
            } 
            else if (this.user_changed_filter_property != null && this.user_changed_filter_property === field.property_name){
                return this.user_changed_filter_is_asc ? 'asc' : 'desc';
            }
            else {
                return false
            }
        },
        set_user_field_filter(field){
            if (field.hasOwnProperty('allow_filter') && field.allow_filter === true) {
                if (this.user_changed_filter_property === field.property_name && this.user_changed_filter_is_asc != null) {
                    this.user_changed_filter_is_asc = !this.user_changed_filter_is_asc;
                }
                else if (this.user_changed_filter_is_asc === null && field.hasOwnProperty('default_filter')) {
                    this.user_changed_filter_is_asc = field.default_filter === 'desc' ? true : false;
                }
                else {
                    this.user_changed_filter_is_asc = true;
                }
                this.user_changed_filter_property = field.property_name;

            }

        },
        sort_rows(raw_data_rows, property, asc_or_desc, property_type){
            let sorted_rows = [];
            
            switch (property_type) {
                case 'default':
                case 'number':
                case 'checkbox':
                    console.log('default!!!');
                    sorted_rows = asc_or_desc === 'desc' ?
                        
                        raw_data_rows.sort(function(rowA, rowB){
                            return rowB[property] - rowA[property];
                        }) 
                        :
                        raw_data_rows.sort(function(rowA, rowB){
                            return rowA[property] - rowB[property];
                        });
                    break;

                case 'date':
                    console.log('date!!!');
                    sorted_rows = asc_or_desc === 'desc' ?
                        
                        raw_data_rows.sort(function(rowA, rowB){
                            let dateA = new Date(rowA[property] + 'T01:00');
                            let dateB = new Date(rowB[property] + 'T01:00');
                            return dateB - dateA;
                        }) 
                        :
                        raw_data_rows.sort(function(rowA, rowB){
                            let dateA = new Date(rowA[property] + 'T01:00');
                            let dateB = new Date(rowB[property] + 'T01:00');
                            return dateA - dateB;
                        });
                    break;

                case 'time':
                    console.log('time!!!');
                    sorted_rows = asc_or_desc === 'desc' ?
                        
                        raw_data_rows.sort(function(rowA, rowB){
                            let timeAstart = new Date("1970-01-01 " + rowA[property]);
                            let timeBstart = new Date("1970-01-01 " + rowB[property]);
            
                            return timeBstart - timeAstart;
                        }) 
                        :
                        raw_data_rows.sort(function(rowA, rowB){
                            let timeAstart = new Date("1970-01-01 " + rowA[property]);
                            let timeBstart = new Date("1970-01-01 " + rowB[property]);
            
                            return timeAstart - timeBstart;
                        });
                    break;

                case 'text':
                    console.log('text!!!');
                    sorted_rows = asc_or_desc === 'desc' ?
                        
                        raw_data_rows.sort(function(rowA, rowB){
                            return rowB[property].localeCompare(rowA[property], 'pl', { sensitivity: 'base' });
                        }) 
                        :
                        raw_data_rows.sort(function(rowA, rowB){
                            return rowA[property].localeCompare(rowB[property], 'pl', { sensitivity: 'base' });
                        });
                    break;

                default:
                    console.log('error message: \n you\'ve tried to sort unhandled data type');
            } 
            console.log('sorted');
            console.log(sorted_rows)
            return sorted_rows;
        }
    },

    computed:{
        is_view_mobile(){
            return this.window_width > this.options.start_mobile_view_px ? true : false;
        },
        filtered_data_rows(){
            let copied_data_rows = this.mock_data_rows.slice();
            if (this.user_changed_filter_property != null && this.user_changed_filter_is_asc != null){
                console.log('user_filer');
                return this.sort_rows(copied_data_rows, 
                    this.user_changed_filter_property,
                    this.user_changed_filter_is_asc === true ? 'asc' : 'desc',
                    this.mock_field_options.find(f => f.property_name === this.user_changed_filter_property).type
                );
            }
            else if (this.mock_field_options.find(f => typeof f.default_filter === 'string')) {
                // this.mock_field_options.find(f => typeof f.default_filter === 'string').
                console.log('default_filter');
                return this.sort_rows(copied_data_rows, 
                    this.mock_field_options.find(f => typeof f.default_filter === 'string').property_name,
                    this.mock_field_options.find(f => typeof f.default_filter === 'string').default_filter,
                    this.mock_field_options.find(f => typeof f.default_filter === 'string').type
                );
            }
            else {
                return copied_data_rows;
            }
        }
    },

    created() {
        window.addEventListener("resize", this.resize_handler);
    },

    destroyed() {
        window.removeEventListener("resize", this.resize_handler);
    },

    mounted(){
        this.window_width = window.innerWidth;
    },

    template: `
    <div class="PN-table-wrapper" id="table-ref" ref="table-ref">
        [[ filtered_data_rows ]]
        <div v-if="is_view_mobile">
            <table class="table styled-table">
                <thead>
                <tr>
                    <th v-for="field in mock_field_options" scope="col">
                        <div v-on:click="set_user_field_filter(field)" class="d-flex inline-flex justify-content-center">
                        [[ field.title ]]
                        <div v-if="filter_triangle_to_show(field) === 'asc'" class="ms-1">&#x25B4</div>
                        <div v-else-if="filter_triangle_to_show(field) === 'desc'" class="ms-1">&#x25BE</div>
                        </div>
                    </th>
                    <!--
                    <th scope="col">Start zmiany</th>
                    <th scope="col">Koniec zmiany</th>
                    <th scope="col">Nazwa</th>
                    <th scope="col">Skrót</th>
                    <th scope="col">Zapotrzebowanie</th>
                    <th scope="col">Kolor</th>
                    <th scope="col">W użyciu</th>
                    <th scope="col">Zapisz</th>
                    <th scope="col">Usuń</th> -->
                </tr>
                </thead>

                <tbody>
                    <tr v-for="(row, i) in filtered_data_rows">
                        <td v-for="field in mock_field_options">[[ row[field.property_name] ]]</td>
                    </tr>
                <!--
                <tr v-for="(shiftType, i) in shiftType_list" :key="shiftType.id">
                    <td><input type="time" class="form-control" v-model="shiftType.hour_start"></td>
                    <td><input type="time" class="form-control" v-model="shiftType.hour_end"></td>
                    <td><input type="text" class="form-control" v-model="shiftType.name"></td>
                    <td><input type="text" class="form-control" v-model="shiftType.shift_code"></td>
                    <td><input type="number" class="form-control" v-model="shiftType.demand"></td>

                    <td><input type="color" class="form-control form-control-color" v-model="shiftType.color"
                                id="colorInput"
                                title="Wybierz kolor zmiany wyświetlany w grafiku"></td>
                    <td><input type="checkbox" class="form-check-input" value="" v-model="shiftType.is_used"></td>
                    <td>
                        <button v-on:click="change_shiftType(i)" type="button"
                                class="btn btn-primary table-buttons"><i class="material-icons">save</i></button>
                    </td>
                    <td>
                        <button v-on:click="remove_shiftType(shiftType.id)" type="button"
                                class="btn btn-danger table-buttons"><i class="material-icons">delete</i></button>
                    </td>
                </tr>
                -->

                </tbody>
                
            </table>
        </div>
        <div v-else>
            <div v-for="(row, i) in filtered_data_rows" class="card position-relative mb-1" v-on:click="set_row_to_edit_mobile(row)"
                data-bs-toggle="modal" data-bs-target="#editRowModal" style="cursor: pointer">
                <div class="card-body">
                    <h5 class="card-title" v-if="mock_field_options.find(f => f.highlighted === true)"> 
                        [[ row[mock_field_options.find(f => f.highlighted == true).property_name] ]]
                    </h5>
                    <div v-for="field in mock_field_options">
                        <div v-if="field.highlighted === undefined || field.highlighted === false">
                            [[ field.title ]] : [[ row[field.property_name] ]]
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- MODALS -->
    <div class="modal fade" id="editRowModal" tabindex="-1" aria-labelledby="editRowModalLabel"
                aria-hidden="true">
            <div class="modal-dialog" style="max-width: 800px">
                <div class="modal-content">
                    <form v-on:submit.prevent="edit_row_datatable">
                        <div class="modal-header">
                            <h5 class="modal-title" id="editRowModaLabel">Edycja</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"
                                    aria-label="Close"></button>
                        </div>

                        <div class="modal-body">
                            <div class="row g-3 d-flex align-items-center">

                                <div v-for="field in mock_field_options">
                                    <div v-if="field.editable">
                                        <div class="col-4">
                                            <label class="form-label modal-style">[[ field.title ]]</label>
                                        </div>
                                        <div class="col=8" v-if="row_to_edit_mobile != null && field.type === 'checkbox'">
                                            <input :type="field.type" class="form-check-input" v-model="row_to_edit_mobile[field.property_name]" required>
                                        </div>
                                        <div class="col=8" v-else-if="row_to_edit_mobile != null && field.type === 'color'">
                                            <input :type="field.type" class="form-control form-control-color" v-model="row_to_edit_mobile[field.property_name]" required>
                                        </div>
                                        <div class="col=8" v-else-if="row_to_edit_mobile != null">
                                            <input :type="field.type" class="form-control" v-model="row_to_edit_mobile[field.property_name]" required>
                                        </div>
                                    </div>
                                </div>
                                <!--
                                <div class="col-4">
                                    <label for="shiftStartDate" class="form-label modal-style" required>Start
                                        zmiany</label>
                                </div>
                                <div class="col-8">
                                    <input type="time" class="form-control" v-model="hour_start"
                                            id="shiftStartDate" required>
                                </div>
                                <div class="col-4">
                                    <label for="shiftEndDate" class="form-label modal-style" required>Koniec
                                        zmiany</label>
                                </div>
                                <div class="col-8">
                                    <input type="time" class="form-control" v-model="hour_end" id="shiftEndDate"
                                            required>
                                </div>
                                <div class="col-4">
                                    <label for="shiftName" class="form-label modal-style" required>Nazwa</label>
                                </div>
                                <div class="col-8">
                                    <input type="text" class="form-control" v-model="name" id="shiftName"
                                            required>
                                </div>
                                <div class="col-4">
                                    <label for="shiftName" class="form-label modal-style" required>Skrót</label>
                                </div>
                                <div class="col-8">
                                    <input type="text" class="form-control" v-model="shift_code" id="shiftName"
                                            required>
                                </div>


                                <div class="col-4">
                                    <label for="demand" class="form-label modal-style">Zapotrzebowanie</label>
                                </div>
                                <div class="col-8">
                                    <input type="number" class="form-control" v-model="demand" id="demand"
                                            required>
                                </div>

                                <div class="col-4">
                                    <label for="color" class="form-label modal-style">Kolor</label>
                                </div>
                                <div class="col-8">
                                    <input type="color" class="form-control" v-model="color" id="color"
                                            required>
                                </div>


                                <div class="col-4">
                                    <label for="isShiftUsed" class="form-label modal-style">W użyciu</label>
                                </div>
                                <div class="col-8 d-flex align-items-center">
                                    <input type="checkbox" class="form-check-input" style="margin: 0px;"
                                            value=""
                                            v-model="is_used" id="isShiftUsed" checked>
                                </div>
                                -->
                            </div>
                        </div>

                        <div class="modal-footer d-flex justify-content-between">
                            <button type="submit" class="btn btn-outline-danger">Usuń</button>
                            <div>
                            <button type="submit" class="btn btn-outline-secondary me-2">Anuluj</button>
                            <button type="submit" class="btn btn-outline-primary">Zapisz</button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
    </div>
  `
}