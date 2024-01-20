export default {
  delimiters: ["[[", "]]"],
  props: { 
    text: {
      type: String,
      required: true
    },
    margin: {
      type: String,
      required: false
    },
    bottom: {
      type: String,
      required: false
    },
    inputData: {
      type: String,
      required: false
    },
  },
  data(){
    return {
      cWidth: null,
      response: null,
      add_data: false,
    }
  },
  methods:{
    calculateLength(){
      return this.text.length
    },
  },
  template: `
  <div class="PN-tooltip-container">
    <slot />
    <div class="PN-tooltip" :style="{ 'margin-left': margin, 'bottom': bottom }">
      <span class="PN-text">
        [[ text ]]
      </span>
    </div>

    <div v-if="add_data" id="field">
      <input :value="inputData" @input="$emit('update:inputData', $event.target.value)">
    </div>
  </div>`
}