<template xmlns:v-slot="http://www.w3.org/1999/XSL/Transform">
  <div>
    <navigation-bar></navigation-bar>

    <b-container v-if="showDocumentHistoryVar">
      <b-table v-if="showTable"
          class="text-left mt-3"
        hover  fixed
        :items="items" :fields="fields"
               @row-clicked="editDocument"
      >
        <template v-slot:cell(index)="data">
          {{ data.index + 1 }}
        </template>
        <template v-slot:cell(id)="row">
          {{ row.item.id }}
        </template>
        <template v-slot:cell(title)="row">
          {{ row.item.title }}
          <b-button title="Delete" variant="outline-light" size="sm"
                    @click="deleteDocument(row.item)">
            <b-icon icon="trash" variant="danger" scale=0.5></b-icon>
          </b-button>
        </template>
      </b-table>

      <b-row class="justify-content-md-center">
        <b-col cols="6">
          <b-button class="my-5"
                    variant="success"
                    @click="newDocument">
            Create New Document
          </b-button>
          <b-button class="my-5 ml-2"
                    variant="success"
                    @click="showDocumentHistory">
            Show Document History
          </b-button>
        </b-col>
      </b-row>
    </b-container>

    <b-container v-else fluid class="d-flex align-items-center justify-content-center" style="height: 100vh;" >
      <b-row>
        <b-col cols="12">
          <b-button
                    variant="success"
                    size="lg"
                    @click="newDocument">
            Create New Document
          </b-button>
        </b-col>
      </b-row>
    </b-container>
  </div>
</template>

<script>
import axios from 'axios';
import NavigationBar from './NavigationBar';
import qs from 'qs';
let urlConfig = require('../url_config');

export default {
  name: 'listing',

  components: {
    NavigationBar
  },

  data: function () {
    return {
      items: [],
      fields: [
        'index',
          'id',
        {
          key: 'title',
          label: 'Title',
          sortable: true
        },
        // {key: 'actions', label: 'Actions'}
      ],
      url_heading: urlConfig.base_url,
      showTable: urlConfig.testing,
      showDocumentHistoryVar: urlConfig.testing,

    };
  },

  methods: {
    getDocuments: function () {
      let uri = this.url_heading;
      axios.get(uri).then((response) => {
        this.items = response.data;
      }).catch(function (error) {
        alert(error.message);
      });
    },

    deleteDocument: function (item) {
      // event.preventDefault();
      console.log('delete called');
      let uri = this.url_heading + item.id + '/' + 'doc_delete' + '/';
      axios.delete(uri).then((response3) => {
        console.log(response3);
        this.items = response3.data.data;
      }).catch(function (error) {
        alert(error.message);
      });
    },

    newDocument: function () {
      let uri = this.url_heading;
      let location = 'userEdit';
      // Axios does the sending
      axios.post(uri, {
        'title': '',
        'author': '',
        'sections': [],
        'sentences': [],
        'keywords': [],
        'articles': [],
        'suggested_links': [],
        'documentHistories': []
      }).then((response) => {
        this.$router.push({name: location, params: {id: response.data.id}});
      }).catch(function (error) {
        alert(error.message);
      });
    },


    editDocument: function (item) {
      let location = 'userEdit';
      this.$router.push({
        name: location,
        params: {id: item.id}
      });
    },

    showDocumentHistory: function () {
      // change variant="success", to disabled
      let location = 'showDocumentHistories';
      this.$router.push({
        name: location,
        //params: {id: item.id}
      });
    },
  },

  beforeMount: function () {
    this.getDocuments();
  }
};
</script>

<style scoped>
</style>
