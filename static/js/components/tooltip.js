export default {
  delimiters: ["[[", "]]"],
  props: { 
    text: {
      type: String,
      required: true
    }
  },
  template: `
  <div class="PN-tooltip-container">
    <slot />
    <div
      class="PN-tooltip"
    >
      <span
        class="PN-text"
      >[[ text ]]</span>
    </div>
  </div>`
}