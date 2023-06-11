<template>
  <div>
    <navigation-bar></navigation-bar>
    <b-container>

      <b-row class="mt-4">
        <b-col cols="4">
          <b-form-input v-model="documentID" placeholder="Enter document ID"></b-form-input>
        </b-col>
        <b-col cols="4">
          <b-button class="mx-5"
                    variant="success"
                    @click="getDocumentHistory">
            Get Document History
          </b-button>
        </b-col>
        <b-col cols="4"></b-col>
      </b-row>

      <b-row class="mt-2">
        <h2>{{documentModel.title}}</h2>
      </b-row>

      <b-row class="my-3">
        <h4 class="mx-2">Histories</h4>
      </b-row>

      <b-row v-for="(history, index) in documentModel.documentHistories" :key="index" class="my-5">
        <b-col cols="8">
          <b-row class="justify-content-center align-items-center">
            <b-col cols="6">
              <p>Timestamp: {{history.timestamp}}</p>
            </b-col>
            <b-col cols="2">
              <b-button variant="info"
                        class="mb-2"
                        size="sm"
                        @click="getDiff(history, index)">
                See Diff
              </b-button>
            </b-col>
            <b-col cols="2">
              <b-button variant="info"
                        class="mb-2"
                        size="sm"
                        @click="showOriginal(history, index)">
                See Orig
              </b-button>
            </b-col>
          </b-row>
          <vue-editor id="quill_editor"
                      ref="quill_editor"
                      class="mb-3"
                      v-model="editorContents[index].text"
                      disabled
                      :editorToolbar="customToolbar"
          />
        </b-col>
        <b-col cols="4">
          <h5 class="my-3">Article List</h5>
          <p class="my-2">{{history.articleList}}</p>
        </b-col>
      </b-row>
<!--------------------------------------------------------------------------------------------->
      <b-row v-if="getDocumentHistoryButtonClicked">
        <b-col cols="8">
          <b-row>
            <b-col cols="6">
              <h5>==Current Document==</h5>
            </b-col>
            <b-col cols="2">
              <b-button variant="info"
                        class="mb-2"
                        size="sm"
                        @click="getDiff(documentModel, index=-67)">
                See Diff
              </b-button>
            </b-col>
            <b-col cols="2">
              <b-button variant="info"
                        class="mb-2"
                        size="sm"
                        @click="showOriginal(documentModel, index=-67)">
                See Orig
              </b-button>
            </b-col>
          </b-row>
          <vue-editor id="quill_editor2"
                      ref="quill_editor2"
                      class="my-3"
                      v-model="currentDocumentEditor"
                      disabled
                      :editorToolbar="customToolbar"
          />
        </b-col>
        <b-col cols="4">
          <h5 class="my-3">Article List</h5>
          <p class="my-2">{{documentModel.articles.map(article => article.url).join('\n')}}</p>
        </b-col>
      </b-row>

    </b-container>
  </div>
</template>

<script>
    import NavigationBar from "./NavigationBar";
    import axios from "axios";
    import {Quill, VueEditor} from "vue2-editor";
    import DocumentModel from '../models/DocumentModel';
    let urlConfig = require('../url_config');

    export default {
      name: "ShowDocumentHistory",
      components: {
        NavigationBar,
        VueEditor,
      },
      data: function () {
        let document = new DocumentModel();
        return {
          editorContents: [],
          currentDocumentEditor: "",
          getDocumentHistoryButtonClicked: false,
          documentID: null,
          documentModel: document,
          loading_spinner: {
            show: false,
            label: ''
          },
          //documentTitle: 'No title',
          //histories: [],
          alertText: '',
          customToolbar: [
            ['bold', 'italic', 'underline'],
            [{'list': 'ordered'}, {'list': 'bullet'}],
            ['image', 'code-block'],
            // ['save'],
            // ['addLink'], ['showLinks'], ['generateSummary'],
          ],
        }
      },
      // watch helps to keep track of some variables
      watch: {
        // documentModel: {
        // },
        // editorContents: {
        // },
        // currentDocumentEditor: {
        // }
      },
      methods: {
         getDocumentHistory (){
          this.getDocumentHistoryButtonClicked = true;
          this.documentModel.load(this.documentID).then(() => {
            let x;
            for(x=0; x<this.documentModel.documentHistories.length; x++){
              console.log("here1")
              // this.editorContents[x] = JSON.parse(JSON.stringify(this.documentModel.documentHistories[x]))
              this.$set(this.editorContents, x, JSON.parse(JSON.stringify(this.documentModel.documentHistories[x])))
              console.log("this.editorContents")
              console.log(this.editorContents)
              console.log("here2")
            }
            console.log("here3")
            this.currentDocumentEditor = (' ' + this.documentModel.text).slice(1)
            // this.currentDocumentEditor = Object.assign({}, this.currentDocumentEditor, (' ' + this.documentModel.text).slice(1))
            console.log("here4")
           })

          // let x;
          // for(x=0; x<this.documentModel.documentHistories.length; x++){
          //   console.log("here1")
          //   this.editorContents = JSON.parse(JSON.stringify(this.documentModel.documentHistories[x]))
          //   console.log("here2")
          // }
          // console.log("here3")
          // this.currentDocumentEditor = (' ' + this.documentModel.text).slice(1)
          // console.log("here4")
        },

        getDiff: function(historyOrCurrent, index){
          let Delta = Quill.import('delta');
          let quillName = "";
          let adjusted = null;

          let prevDocument = null;
          let currentDocumentDelta = new Delta()
          currentDocumentDelta.insert(historyOrCurrent.text);

          //check if input is current-doc or one of doc-histories
          if("title" in historyOrCurrent){ // if it's the current document
            prevDocument = this.documentModel.documentHistories
                [this.documentModel.documentHistories.length - 1];
            quillName = "quill_editor2"
          }else{
            let func = ((element) =>  element.id === historyOrCurrent.id);
            index = this.documentModel.documentHistories.findIndex(func);
            if(index != 0 && index != -1){
              prevDocument = this.documentModel.documentHistories[index - 1]
            }
            quillName = "quill_editor"
          }

          // So, first version of document is not evaluated since
          // there's no previous version to compare
          if(prevDocument != null){
            let prevDocumentDelta = new Delta()
            prevDocumentDelta.insert(prevDocument.text)
            console.log("prevDocumentDelta")
            console.log(prevDocumentDelta)

            console.log("currentDocumentDelta")
            console.log(currentDocumentDelta)

            let observedChanges = prevDocumentDelta.diff(currentDocumentDelta)
            console.log("observedChanges")
            console.log(observedChanges)
            for(let i = 0; i < observedChanges.ops.length; i++){
                let op = observedChanges.ops[i];
                // if the change was an insertion
                if (op.hasOwnProperty('insert')) {
                  // color it green
                  op.attributes = {
                    background: "#cce8cc",
                    color: "#003700"
                  };
                }
                // if the change was a deletion
                if (op.hasOwnProperty('delete')) {
                  // keep the text
                  op.retain = op.delete;
                  delete op.delete;
                  // but color it red and struckthrough
                  op.attributes = {
                    background: "#e8cccc",
                    color: "#370000",
                    strike: true
                  };
                }
            }
            adjusted = prevDocumentDelta.compose(observedChanges);
            console.log("adjusted")
            console.log(adjusted)
          }
          console.log("this")
          console.log(this)
          if(index == -67){
            this.$refs[quillName].quill.setContents(prevDocument != null
                ? adjusted:currentDocumentDelta);
          }
          else{
            this.$refs[quillName][index].quill.setContents(prevDocument != null
                ? adjusted:currentDocumentDelta);
          }
        },
        showOriginal: function (historyORcurrentdoc, index) {
           let quillName = index==-67 ? "quill_editor2":"quill_editor"
          let Delta = Quill.import('delta');

          let currentDocumentDelta = new Delta()
          currentDocumentDelta.insert(historyORcurrentdoc.text);

          if(index == -67){
            this.$refs[quillName].quill.setContents(currentDocumentDelta);
          }
          else{
            this.$refs[quillName][index].quill.setContents(currentDocumentDelta);
          }
        }
      }
    }
</script>

<style scoped>
#quill_editor .ql-editor {
  min-height: 300px;
}
</style>
