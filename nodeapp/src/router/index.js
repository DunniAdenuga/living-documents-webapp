import Vue from 'vue'
import Router from 'vue-router'
// components
import List from '../components/List'
import UserEdit from "../components/UserEdit";
import ShowTreeComponent from "../components/ShowTreeComponent";
import ShowDocumentHistory from "../components/ShowDocumentHistory";


Vue.use(Router)

export default new Router({
  routes: [
    { path: '/',        name: 'list', component: List},
    { path: '/userEdit/:id', name: 'userEdit', component: UserEdit},
    { path: '/showTree/:id', name: 'showTree', component:ShowTreeComponent},
    { path: '/showDocumentHistory', name: 'showDocumentHistories', component: ShowDocumentHistory}
  ]
});
