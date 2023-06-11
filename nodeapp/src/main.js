// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.

// Require Froala Editor js file.
require('froala-editor/js/froala_editor.pkgd.min')

// Require Froala Editor css files.
require('froala-editor/css/froala_editor.pkgd.min.css')
require('froala-editor/css/froala_style.min.css')

import Vue from 'vue'
import App from './App'
import Vmodal from 'vue-js-modal'
import VueMaterial from 'vue-material'
import Vuesax from 'vuesax'
import 'vue-material/dist/vue-material.min.css'
// import Vuetify from 'vuetify'

import router from './router'

import 'vuesax/dist/vuesax.css'
import 'material-icons/iconfont/material-icons.css';

//bootstrap
// import BootstrapVue from 'bootstrap-vue'
import {BootstrapVue, BootstrapVueIcons } from 'bootstrap-vue'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'

import VueFroala from 'vue-froala-wysiwyg'

Vue.config.productionTip = false
Vue.use(BootstrapVue)
Vue.use(BootstrapVueIcons)
Vue.use(Vmodal)
Vue.use(VueMaterial)
Vue.use(VueFroala)
Vue.use(Vuesax)
// Vue.use(Vuetify)
//Vue.component('editor', require('./components/Editor'));

/* eslint-disable no-new */
var vm = new Vue({
  el: '#app',
  router,
  components: { App },
  template: '<App/>'
})

global.vm = vm
