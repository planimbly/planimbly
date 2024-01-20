describe('template spec', () => {
  beforeEach(() => {   
    cy.on('uncaught:exception', (err, runnable) => {
      return false
     })

    cy.login()
  })

  Cypress.Commands.add('login', () => {
    cy.session(
      'login session',
      () => {
        cy.visit('/accounts/login')
        cy.get('#id_username').clear('a');
        cy.get('#id_username').type('admin');
        cy.get('#id_password').clear('A');
        cy.get('#id_password').type('Admin123Admin123');
        cy.get('.btn').click();
        cy.url().should('include', '/schedules/schedule_manage/')
      },
      {
        validate: () => {
          cy.getCookie('csrftoken').should('exist')
        },
      }
    )
  })

  it('check sidebar action', () => {
    cy.visit('/schedules/schedule_manage/')
    cy.get('#burger').click();
    cy.get('#sidebar').should('be.visible')
    cy.get('#burger').click();
    cy.get('#sidebar').should('not.be.visible')
  })

  it('check sidebar movement', () => {
    cy.visit('/schedules/schedule_manage/')
    cy.get('#burger').click();
    cy.get('.sidebar-list > :nth-child(1)').click();

    cy.url().should('include', '/organizations')
  })

  it('check tooltip pop-up visability', () => {
    cy.visit('/organizations/workplace_closing/')
    cy.get('.PN-tooltip-container').realHover()
    cy.get('.PN-tooltip').should('be.visible')
  })

  it('check responsiveness', () => {
    cy.visit('/schedules/schedule_manage/')
    cy.viewport(600, 1900)
    cy.get('.calendar-big').should('have.css', 'flex-direction', 'column');
    cy.viewport(1920, 900)
    cy.get('.calendar-big').should('have.css', 'display', 'grid');
  })

})