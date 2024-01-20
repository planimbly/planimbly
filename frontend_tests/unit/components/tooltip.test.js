import { expect, test } from 'vitest'
import { mount } from '@vue/test-utils'
import tooltip from '../../../static/js/components/tooltip.js'

test('test rendering a tooltip component and passing data', () => {
  const wrapper = mount(tooltip, {
      props: {
          text: "test string"
        },
      data () {
          return {
            cWidth: 1,
          }
      }
  })

  expect(wrapper.text()).toBe('test string')

  expect(wrapper.find('#field').exists()).toBe(false)
})

test('test method execution', () => {
  const wrapper = mount(tooltip, {
      props: {
          text: "test string"
        },
      data () {
          return {
            cWidth: 1,
          }
      }
  })
  
  expect(wrapper.vm.calculateLength()).toBe(11)
})


test('test conditional rendering', () => {
  const wrapper = mount(tooltip, {
      props: {
          text: "test string"
        },
      data () {
          return {
            add_data: true,
          }
      }
  })

  expect(wrapper.find('#field').exists()).toBe(true)
})

test('test v-model changes', async () => {
  const wrapper = mount(tooltip, {
      props: {
          text: "test string",
          'onUpdate:inputData': (e) => wrapper.setProps({ inputData: e })
        },
      data () {
          return {
            add_data: true,
          }
      }
  })
  
  expect(wrapper.props('inputData')).toBe(undefined)
  
  await wrapper.find('input').setValue('test')

  expect(wrapper.props('inputData')).toBe('test')
})

test('test slot capability', () => {
  const wrapper = mount(tooltip, {
    slots: {
      default: 'slot test'
    },
    props: {
        text: "test string",
      },
    data () {
        return {
          cWidth: 1,
        }
    }
})

  expect(wrapper.html()).toContain('slot test')
})