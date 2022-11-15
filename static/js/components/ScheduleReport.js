export default {
    delimiters: ["[[", "]]"],

    props: {
      year: Number,
      month: Number, //1-12
      unit_id: Number,
      workplaces: Object,
      attach_days_employees_report: Boolean,
    },

    data () {
      return {
        
      }
    },
    
    methods:{

    },

    computed:{
      
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

    </div>
  `
}