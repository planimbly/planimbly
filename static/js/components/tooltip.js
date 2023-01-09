export default {
  delimiters: ["[[", "]]"],
  props: { 
    text: {
      type: String,
      required: true
    },
    elementid: {
      type: String,
      required: true
    },
  },
  data(){
    return {
      cWidth: null,
    }
  },
  methods: {

  },
  computed: {
    updateId(){
      if ( document.getElementById(this.elementid) != null) {
        this.cWidth = document.getElementById(this.elementid).clientWidth
        console.log(this.cWidth)
      }
    }
  },
  template: `
  <div class="PN-tooltip-container">
    [[ updateId ]]
    <slot />
    <div class="PN-tooltip">
      <span class="PN-text">
        [[ text ]]
      </span>
    </div>
  </div>`
}