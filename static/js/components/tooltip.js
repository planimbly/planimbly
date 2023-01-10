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
  },
  data(){
    return {
      cWidth: null,
    }
  },
  template: `
  <div class="PN-tooltip-container">
    <slot />
    <div class="PN-tooltip" :style="{ 'margin-left': margin, 'bottom': bottom }">
      <span class="PN-text">
        [[ text ]]
      </span>
    </div>
  </div>`
}