export default {
    delimiters: ["[[", "]]"],

    props: {
      
    },

    data () {
      return {
        
      }
    },
    
    methods:{
      printToPdf(){
        alert(this.$refs.report.innerText);
        var mywindow = window.open("", "PRINT", 
                "height=400,width=600");
  
        mywindow.document.write(this.$refs.report.innerHTML);
  
        mywindow.document.close();
        mywindow.focus();
  
        mywindow.print();
        mywindow.close();
  
        return true;
      }
    },

    computed:{
      
    },

    template: `
    <button type="button" class="btn btn-primary" @click="printToPdf">DO PDF</button>
    <div ref='report'>
        <h1>Hello world</h1>
    </div>
    `
}