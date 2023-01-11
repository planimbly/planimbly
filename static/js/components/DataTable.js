export default {
    delimiters: ["[[", "]]"],

    emits: ['rows-sent-to-delete', 'rows-sent-to-update', 'click-row'],

    props: {
        /*
        [{
            title: ...,
            editable: false/true,
            property_name: ...,
            type: ...,
            allow_filter: true/false,
            default_filter: asc/desc,
            highlighted: true,
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
                allow_special_edit_mode: true,
                allow_modal_edit_on_mobile: true,
                allow_modal_edit_on_desktop: false,
                always_mobile_mode: false,
            },
        }

    },

    data () {
      return {
        window_width: 0,
        row_to_edit_mobile: null,
        user_changed_filter_property: null,
        user_changed_filter_is_asc: null,
        special_edit_mode: false,
      }
    },

    methods:{
        resize_handler(e){
            this.window_width = window.innerWidth;
        },

        register_row_click(row){
            if (!this.special_edit_mode){
                this.$emit('click-row', row);
            }  
        },

        hide_modal(modal_id){
            let editRowModalElement = document.getElementById(modal_id)
            let editRowModal= bootstrap.Modal.getInstance(editRowModalElement)
            editRowModal.hide();
        },

        send_rows_to_delete(rows){
            this.$emit('rows-sent-to-delete', rows);
        },

        send_rows_to_update(rows){
            this.$emit('rows-sent-to-update', rows);
        },

        edit_row_datatable(row){
            swal({
                title: "Czy chcesz zatwierdzić zmiany",
                icon: "info",
                buttons: true
            })
                .then((willAdd) => {
                    if (willAdd) {
                        this.hide_modal('editRowModal');
                        this.send_rows_to_update([row]);
                    }
                });
        },

        delete_row_datatable(row){
            
            swal({
                title: "Czy na pewno chcesz usunąć?",
                icon: "warning",
                buttons: true,
                dangerMode: true,
            })
                .then((willDelete) => {
                    if (willDelete) {
                        this.hide_modal('editRowModal');
                        this.send_rows_to_delete([row]);
                    }
                });
        },

        set_row_to_edit_mobile(row){
            this.row_to_edit_mobile = Object.assign({}, row);
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
            return sorted_rows;
        }
    },

    computed:{
        is_view_desktop(){
            return (this.window_width > this.options.start_mobile_view_px) && (!this.options.always_mobile_mode) ? true : false;
        },
        filtered_data_rows(){
            let copied_data_rows = []
            if (this.data_rows && typeof this.data_rows !== undefined) {
                copied_data_rows = this.data_rows.slice();
            }
            if (this.user_changed_filter_property != null && this.user_changed_filter_is_asc != null){
                return this.sort_rows(copied_data_rows, 
                    this.user_changed_filter_property,
                    this.user_changed_filter_is_asc === true ? 'asc' : 'desc',
                    this.fields_options.find(f => f.property_name === this.user_changed_filter_property).type
                );
            }
            else if (this.fields_options && this.fields_options.find(f => typeof f.default_filter === 'string')) {
                return this.sort_rows(copied_data_rows, 
                    this.fields_options.find(f => typeof f.default_filter === 'string').property_name,
                    this.fields_options.find(f => typeof f.default_filter === 'string').default_filter,
                    this.fields_options.find(f => typeof f.default_filter === 'string').type
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
        
        <div v-if="is_view_desktop">
            <table class="table styled-table table-hover">
                <thead>
                <tr>
                    <th v-for="field in fields_options" scope="col">
                        <div v-on:click="set_user_field_filter(field)" class="d-flex inline-flex justify-content-center" style="cursor: pointer">
                        [[ field.title ]]
                        <div v-if="filter_triangle_to_show(field) === 'asc'" class="ms-1" style="cursor: pointer">&#x25B4</div>
                        <div v-else-if="filter_triangle_to_show(field) === 'desc'" class="ms-1" style="cursor: pointer">&#x25BE</div>
                        </div>
                    </th>
                </tr>
                </thead>

                <tbody>
                    <tr v-for="(row, i) in filtered_data_rows" v-on:click="set_row_to_edit_mobile(row); register_row_click(row);" 
                        v-bind="{'data-bs-toggle': (options.allow_modal_edit_on_desktop ? 'modal' : 'none')}" data-bs-target="#editRowModal" style="cursor: pointer">
                        <td v-for="field in fields_options">
                            <div v-if="field.type === 'checkbox' && row[field.property_name] === true">tak</div>
                            <div v-else-if="field.type === 'checkbox' && row[field.property_name] === false">nie</div>
                            <div v-else-if="field.type === 'color'" :style="{ 'background-color': row[field.property_name] }"
                              class="PN-color-display-wrapper"> <div class="PN-color-display" :style="{ 'background-color': row[field.property_name] }">&nbsp</div>
                            </div>
                            <div v-else> [[ row[field.property_name] ]] </div>
                        </td>
                    </tr>

                </tbody>
                
            </table>
        </div>
        <div v-else>
            <div v-for="(row, i) in filtered_data_rows" class="card position-relative mb-1 PN-hover-card" v-on:click="set_row_to_edit_mobile(row); register_row_click(row);"
                v-bind="{'data-bs-toggle': (options.allow_modal_edit_on_mobile ? 'modal' : 'none')}" data-bs-target="#editRowModal" style="cursor: pointer">
                <div class="card-body text-center">
                    <h5 class="card-title mb-0" v-if="fields_options && fields_options.find(f => f.highlighted === true)"> 
                        [[ row[fields_options.find(f => f.highlighted == true).property_name] ]]
                    </h5>
                    <div v-for="field in fields_options">
                        <div v-if="field.highlighted === undefined || field.highlighted === false">
                            <div v-if="field.type === 'color'" class="PN-color-display-wrapper">
                                Kolor :   
                                <div class="PN-color-display ms-2" :style="{ 'background-color': row[field.property_name] }">&nbsp</div> 
                            </div>
                            <div v-else-if="field.type === 'checkbox' && row[field.property_name] === true">[[ field.title ]] : tak</div>
                            <div v-else-if="field.type === 'checkbox' && row[field.property_name] === false">[[ field.title ]] : nie</div>
                            <div v-else> [[ field.title ]] : [[ row[field.property_name] ]] </div>
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
                    <form v-on:submit.prevent="edit_row_datatable(row_to_edit_mobile)">
                        <div class="modal-header">
                            <h5 class="modal-title" id="editRowModaLabel">Edycja</h5>
                            
                            <button type="button" class="btn-close" data-bs-dismiss="modal"
                                    aria-label="Close"></button>
                        </div>

                        <div class="modal-body">
                            <div class="row g-3 d-flex align-items-center">

                                <div v-for="field in fields_options">
                                    <div v-if="field.editable">
                                        <div class="col-4">
                                            <label class="form-label modal-style">[[ field.title ]]</label>
                                        </div>
                                        <div class="col=8" v-if="row_to_edit_mobile != null && field.type === 'checkbox'">
                                            <input :type="field.type" class="form-check-input" v-model="row_to_edit_mobile[field.property_name]">
                                        </div>
                                        <div class="col=8" v-else-if="row_to_edit_mobile != null && field.type === 'color'">
                                            <input :type="field.type" class="form-control form-control-color" v-model="row_to_edit_mobile[field.property_name]" required>
                                        </div>
                                        <div class="col=8" v-else-if="row_to_edit_mobile != null">
                                            <input :type="field.type" class="form-control" v-model="row_to_edit_mobile[field.property_name]" required>
                                        </div>
                                    </div>
                                    <div v-else>
                                        <div class="col-4">
                                            <label class="form-label modal-style">[[ field.title ]]</label>
                                        </div>
                                        <div class="col=8" v-if="row_to_edit_mobile != null && field.type === 'checkbox'">
                                            <input :type="field.type" class="form-check-input" v-model="row_to_edit_mobile[field.property_name]" disabled>
                                        </div>
                                        <div class="col=8" v-else-if="row_to_edit_mobile != null && field.type === 'color'">
                                            <input :type="field.type" class="form-control form-control-color" v-model="row_to_edit_mobile[field.property_name]" disabled>
                                        </div>
                                        <div class="col=8" v-else-if="row_to_edit_mobile != null">
                                            <input :type="field.type" class="form-control" v-model="row_to_edit_mobile[field.property_name]" disabled>
                                        </div>
                                    </div>
                                </div>

                            </div>
                        </div>

                        <div class="modal-footer d-flex justify-content-between">
                            <button type="button" class="btn btn-outline-danger" v-on:click="delete_row_datatable(row_to_edit_mobile)">Usuń</button>
                            <div>
                            <button type="button" class="btn btn-outline-secondary me-2"
                                data-bs-target="#editRowModal" data-bs-toggle="modal" data-bs-dismiss="modal" aria-label="Close">Anuluj</button>
                            <button v-if="options.editable" type="submit" class="btn btn-primary">Zapisz</button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
    </div>
  `
}