<template>
  <div>
    <navigation-bar/>
    <b-container>

      <b-row class="pl-1" align-h="start">
        <b-col cols="4" id="title" >
          <b-form-input id="input-large"
                        class="text-center"
                        v-model="documentModel.title"
                        size="lg"
                        type="text" placeholder="Enter Title"
                        trim>
          </b-form-input>
        </b-col>
      </b-row>

      <b-row id="for-outline-and-editor" class="text-left">
        <b-col cols="4" id="outline">
          <div class="pl-2">
            <!--            <h3>Outline</h3>-->
            <b-icon icon="card-list" scale=2.0></b-icon>
          </div>

          <div class="px-1 py-2">
            <b-row align-v="center">
              <b-col class="mt-3 mr-1" cols="3">
                <h5><b>Sections</b></h5>
              </b-col>
              <b-col v-if="studyLevel==='all-controls'" class="mt-2" cols="4">
                <b-button v-if="studyLevel==='all-controls'"
                          title="Add New Section"
                          variant="outline-light"
                          @click="onIconAddSectionClicked">
                  <b-icon icon="plus-circle" variant="success" scale=1.2></b-icon>
                </b-button>
              </b-col>
            </b-row>

            <!--            For Introduction -->
            <ul id="introduction" class="pl-3"><li>
              <b-row class="pl-2 justify-content-md-center" align-v="center" >
                <b-col cols="4">
                  <p>Introduction</p>
                </b-col>
                <b-col cols="8" class="mt-1">
                  <b-button v-if="studyLevel==='all-controls'"
                            title="Add Link to Introduction" variant="outline-light" size="sm"
                            @click="onAddLinkClicked()">
                    <b-icon icon="link45deg" variant="success" scale=0.6></b-icon>
                  </b-button>
                  <b-button title="Generate Summary for Introduction" variant="outline-light" size="sm"
                            @click="onGenerateSummaryClicked()">
                    <b-icon icon="download" variant="success" scale=0.6></b-icon>
                  </b-button>
                </b-col>
              </b-row>
              <b-row>
                <b-col>
                  <ul class="pl-2" id="userLinksList">
                    <li v-for="article in this.documentModel.articles" :key="article.id">
                      <b-row>
                        <b-col>
                          <a v-bind:href="article.url" id="eachArticle" ref="eachArticle">{{ getLittleVersion(article.url) }}</a>
                          <b-button v-if="showArticleSentencesTempObj !== article.id" title="See Link Summary Sentences" variant="outline-light" size="sm"
                                    @click="turnOnArticleSentences(article, null)">
                            <b-icon icon="eye" variant="success" scale=0.5></b-icon>
                          </b-button>
                          <b-button v-if="showArticleSentencesTempObj === article.id" title="Hide Link Summary Sentences" variant="outline-light" size="sm"
                                    @click="turnOffArticleSentences">
                            <b-icon icon="eye-slash" variant="success" scale=0.5></b-icon>
                          </b-button>
                          <b-button v-if="studyLevel==='all-controls'"
                                    title="Remove Link" variant="outline-light" size="sm"
                                    @click="onRemoveLinkClicked(article.url)">
                            <b-icon icon="x-circle-fill" variant="danger" scale=0.5></b-icon>
                          </b-button>
                        </b-col>
                      </b-row></li></ul>
                </b-col>
              </b-row>
            </li>
            </ul>

            <!--            Rest of List of Sections -->
            <ul class="pl-3" id="sectionsList" v-for="section in this.documentModel.sections" :key="section.heading"
                v-if="studyLevel==='all-controls'">
              <li>
                <b-row class="pl-2 pt-1" align-v="center">
                  <b-col cols="4">
                    <p>{{section.heading}}</p>
                  </b-col>
                  <b-col cols="8" class="mt-1">
                    <b-button title="Add Link to Section" variant="outline-light" size="sm"
                              @click="onIconAddLinkToSectionClicked(section.heading)">
                      <b-icon icon="link45deg" variant="success" scale=0.6></b-icon>
                    </b-button>
                    <b-button title="Generate Summary for section" variant="outline-light" size="sm"
                              @click="onGenerateSectionSummaryClicked(section.heading)">
                      <b-icon icon="download" variant="success" scale=0.6></b-icon>
                    </b-button>
                    <b-button title="Remove Section" variant="outline-light" size="sm"
                              @click="onRemoveSectionClicked(section)">
                      <b-icon icon="x-circle-fill" variant="danger" scale=0.5></b-icon>
                    </b-button>
                  </b-col>
                </b-row>
                <b-row>
                  <b-col>
                    <ul class="pl-2" id="eachSectionLinksList">
                      <li v-for="article in section.articles" :key="article.id">
                        <b-row>
                          <b-col>
                            <a v-bind:href="article.url" id="eachSectionArticle" ref="eachArticle">{{ getLittleVersion(article.url) }}</a>
                            <b-button v-if="showArticleSentencesTempObj !== article.id" title="See Link Summary Sentences" variant="outline-light" size="sm"
                                      @click="turnOnArticleSentences(article, section)">
                              <b-icon icon="eye" variant="success" scale=0.5></b-icon>
                            </b-button>
                            <b-button v-if="showArticleSentencesTempObj === article.id" title="Hide Link Summary Sentences" variant="outline-light" size="sm"
                                      @click="turnOffArticleSentences">
                              <b-icon icon="eye-slash" variant="success" scale=0.5></b-icon>
                            </b-button>
                            <b-button title="Remove Link" variant="outline-light" size="sm"
                                      @click="onRemoveLinkClicked(article.url, section)">
                              <b-icon icon="x-circle-fill" variant="danger" scale=0.5></b-icon>
                            </b-button>
                          </b-col>
                        </b-row>
                      </li>
                    </ul>
                  </b-col>
                </b-row>
              </li>
            </ul>
          </div>

          <!--          Suggested Sections          -->
          <div class="px-1" v-if="studyLevel==='all-controls'">
            <h5><b>Suggested Sections</b></h5>
            <div>
              <span v-for="keyword in this.documentModel.keywords">
                {{ keyword.text.charAt(0).toUpperCase()+keyword.text.slice(1) + " ::" }} </span>
            </div>
          </div>

          <!--          Suggested Links             -->
          <div class="px-1" v-if="studyLevel==='all-controls'">
            <h5><b>Suggested Links</b></h5>
            <ul class="pl-2" id="suggestedLinksList">
              <li v-for="link in this.documentModel.suggested_links">
                <b-row>
                  <b-col>
                    <a v-bind:href="link.url" id="eachSuggestedLink" ref="eachSuggestedLink">{{ getLittleVersion(link.url) }}</a>
                  </b-col>
                </b-row>
              </li>
            </ul>
          </div>
        </b-col>

        <b-col cols="6" id="and-editor">
          <!-- Quill Editor ---->
          <vue-editor id="quill_editor"
                      ref="quill_editor"
                      v-model="documentModel.text"
                      :editorToolbar="customToolbar"
                      :editorOptions="editorSettings"
                      :disabled="studyLevel === 'no-controls'"
          />
        </b-col>
        <b-col cols="2" id="see-tree-save-doc">
          <b-row>
            <b-button class="mt-5"
                      variant="success"
                      @click="seeTree">
              See Graph
            </b-button>
          </b-row>
          <b-row>
            <b-button v-if="studyLevel != 'no-controls'"
                      class="mt-3"
                      style="position: fixed; width: 15%; "
                      variant="success"
                      @click="onSaveClicked()">
              Save
            </b-button>
          </b-row>
          <b-alert
              :show="dismissCountDown"
              dismissible
              variant="success"
              @dismissed="dismissCountDown=0"
              @dismiss-count-down="countDownChanged"
              style="position: fixed; top: 300px;"
          >
            Document Saved!
          </b-alert>
        </b-col>
      </b-row>


      <!-- --------------------------------------------------------------------------------------------------- -->

      <!-- Modal for adding links -->
      <b-modal id="modalAddLink"
               ref="modalAddLink"
               title="Enter Link"
               @ok="handleAddLinkOKClicked"
      >
        <form @submit.stop.prevent="handleAddLinkSubmit">
          <b-form-input type="text"
                        placeholder="Text Link"
                        v-model="addLink"/>
        </form>
      </b-modal>

      <!-- Modal for adding section names -->
      <b-modal id="modalAddSectionName"
               ref="modalAddSectionName"
               title="Enter Section Name"
               @ok="handleAddSectionNameOKClicked"
      >
        <form @submit.stop.prevent="handleAddSectionNameSubmit">
          <b-form-input type="text"
                        placeholder="Section Name"
                        v-model="sectionName"/>
        </form>
      </b-modal>

      <!-- Modal for adding links to each section -->
      <b-modal id="modalAddLinkToSection"
               ref="modalAddLinkToSection"
               title="Enter Link for Section"
               @ok="handleAddLinkToSectionOKClicked"
      >
        <form @submit.stop.prevent="handleAddLinkToSectionSubmit">
          <b-form-input type="text"
                        placeholder="New Link for each Section"
                        v-model="eachLink"/>
        </form>
      </b-modal>


      <!-- For the overlay spinner -->
      <template>
        <loading
            :show="loading_spinner.show"
            :label="loading_spinner.label">
        </loading>
      </template>

    </b-container>
  </div>
</template>

<script>
import {Quill, VueEditor} from 'vue2-editor';
import loading from 'vue-full-loading';
import { BSidebar, BootstrapVueIcons  } from 'bootstrap-vue'
import NavigationBar from './NavigationBar';
import DocumentModel from '../models/DocumentModel';
let urlConfig = require('../url_config');

export default {
  name: 'UserEdit',

  computed: {
  },

  components: {
    NavigationBar,
    VueEditor,
    Quill,
    BSidebar,
    BootstrapVueIcons,
    loading
  },

  beforeMount: function () {
    // load the document from the backend using the id in the url
    this.id = this.$route.params.id;
    this.documentModel.load(this.$route.params.id);

  },

  mounted: function () {
    // this.onSaveClicked()
    // this.counter = 1
  },

  data: function () {
    let document = new DocumentModel();
    return {
      base_url: urlConfig.summarizer_url,
      loading_spinner: {
        show: false,
        label: ''
      },
      documentModel: document,
      id: '', //documentID

      counter: 0,

      addLink: '',

      sectionName: '',
      eachLink: '',
      currentSectionHeading: '',
      // sections: [], //contains section objects {heading:'', articles: [], sentences: []}

      //disappear-able alert
      dismissSecs: 3,
      dismissCountDown: 0,

      //turn on article sentences
      hideArticleSentences: true,
      tempWholeDocument: null,
      showArticleSentencesTempObj: null,
      //articleInstance: {article: null, showSentences: false},

      //set Study levels
      studyLevel: urlConfig.studyLevel,

      //add generate
      //customToolbar: [[]],
      customToolbar: [
        ['italic'],
        //['underline', 'strike'],
        [{ 'header': 1 }, { 'header': 2 }],
       [{'list': 'ordered'}, {'list': 'bullet'}],
        ['link', 'image'], [{'color': []}],
          ['clean']
        //['image', 'code-block'],
        // ['save'],
        // ['addLink'], ['showLinks'], ['generateSummary'],
      ],
      editorSettings: {
        theme: 'snow',
        // modules: {
        //   clipboard: {
        //     matchVisual: false,
        //   }
        // }
      }
    };
  },

  // watch helps to keep track of some variables
  watch: {
    documentModel: {
    }
  },

  beforeDestroy() {
    // console.log("saving before destroying..")
    // this.onSaveClicked()
  },

  methods: {
    seeTree: function (){
      let self = this
      this.$router.push({
        name: 'showTree',
        params: {id: self.$route.params.id}
      })
    },

    countDownChanged(dismissCountDown){
      this.dismissCountDown = dismissCountDown
    },

    /**
     * Called when the save button at the bottom of the page is clicked, it just calls the document model method to
     * write to backend
     */
    onSaveClicked: function () {
      if(this.loading_spinner.show == false){
        let current_editor_contents = this.$refs.quill_editor.quill.getText()
        let current_editor_contentsHTML = this.$refs.quill_editor.quill.root.innerHTML
        // let current_editor_contents_d = this.$refs.quill_editor.quill.getContents()
        console.log("current editor contents")
        // console.log(current_editor_contents_d)
        console.log(current_editor_contents)
        console.log("current editor contents HTML!")
        // console.log(current_editor_contents_d)
        console.log(current_editor_contentsHTML)
        //would only work for introduction
        this.documentModel.save(current_editor_contents, current_editor_contentsHTML, ()=> {
          this.documentModel.load(this.id)
        }, ()=>{
          alert("Save Failed. Try Again!")
        })
        // window.setInterval(this.onSaveClicked, 600000)
        this.dismissCountDown = this.dismissSecs
      }
    },


    // TODO this is probably all the link stuff that need to be changed
    clearLink: function () {
      this.addLink = '';
    },


    /**
     * When the OK button on the new link modal dialog is clicked we check that they have actually entered a link.
     * TODO This could be better handled by tracking text and disabling/enabling the save button.
     * @param evt
     */
    handleAddLinkOKClicked: function (evt) {
      // Prevent modal from closing
      evt.preventDefault();
      if (!this.addLink) {
        alert('Please enter link for article location');
      } else {
        this.handleAddLinkSubmit();
      }
    },

    /**
     *
     */
    handleAddLinkSubmit: function () {
      // this.documentModel.addUrl(this.addLink);
      this.documentModel.articles.push({url: this.addLink, text: '', sentences: []})
      this.clearLink();
      this.$refs.modalAddLink.hide();
    },

    ///////////////////////////////////////////////////////////////////////
    /**
     * */

    onIconAddSectionClicked: function () {
      this.$refs.modalAddSectionName.show()
    },

    handleAddSectionNameOKClicked: function () {
      // evt.preventDefault()
      if(!this.sectionName){
        alert('Please enter new section name');
      }else{
        //let existing_section = this.documentModel.sections.find(obj => obj.heading == this.sectionName)
        //if(existing_section == null){
        this.handleAddSectionNameSubmit();
        //}
      }
    },

    handleAddSectionNameSubmit: function (){
      this.documentModel.sections.push({heading: this.sectionName, position: -1, articles: [], sentences: []})
      // console.log(this.documentModel.sections)
      this.sectionName = ''
      this.$refs.modalAddSectionName.hide()
    },
/////////////////////////////////////////////////////////////
    onIconAddLinkToSectionClicked: function (currentSection){
      this.currentSectionHeading = currentSection
      this.$refs.modalAddLinkToSection.show()
    },

    handleAddLinkToSectionOKClicked: function (evt){
      evt.preventDefault()
      if(!this.eachLink){
        alert('Please enter link for  section');
      }else{
        this.handleAddLinkToSectionSubmit()
      }
    },

    handleAddLinkToSectionSubmit: function(){
      // let existing_section = this.documentModel.sections.find(obj => obj.heading == this.currentSectionHeading)
      for (let section of this.documentModel.sections){
        if(section.heading == this.currentSectionHeading){
          section.articles.push({url: this.eachLink, text: '', sentences: []})
          break
        }
      }
      // existing_section.articles.append({url: this.eachLink, text: ''})
      this.$refs.modalAddLinkToSection.hide()
      this.eachLink = ''
    },

    //////////////////////////////////////
    /* Links per document (different from links per section above)*/
    onAddLinkClicked: function () {
      this.clearLink()
      this.$refs.modalAddLink.show();
    },

    onRemoveLinkClicked: function (article_url, section=null) {
      let temp_object = null
      if (section === null){
        temp_object = this.documentModel
      }else{
        temp_object = section
      }
      let x = 0
      for(let each_article of temp_object.articles){
        if(each_article.url == article_url){
          let removed_article = temp_object.articles.splice(x, 1)[0]
          let temp_document_sentences = JSON.parse(JSON.stringify(temp_object.sentences))

          console.log("removed_ article")
          console.log(removed_article)
          console.log("article_sentences")
          console.log(removed_article.sentences)
          console.log("document sentences")
          console.log(temp_object.sentences)

          for(let article_sentence of removed_article.sentences){
            // if(temp_document_sentences.includes(sentence)){}
            let y = 0
            for(let document_sentence of  temp_document_sentences){
              if(article_sentence.text === document_sentence.text){
                temp_document_sentences.splice(y, 1)
              }
              y = y + 1
            }
          }

          temp_object.sentences = temp_document_sentences
          console.log("new document sentences")
          console.log(temp_object.sentences)
          break
        }
        x = x + 1
      }
    },

    onRemoveSectionClicked: function (section) {
      let temp_object = this.documentModel
      let x = 0
      for(let each_section of temp_object.sections) {
        if (each_section.id == section.id) {
          let removed_section = temp_object.sections.splice(x, 1)[0]
          // let temp_document_sentences = JSON.parse(JSON.stringify(temp_object.sentences))

          console.log("removed_section")
          console.log(removed_section)
          console.log("document")
          console.log(this.documentModel)
        }
        x= x+1
      }
    },

    onGenerateSummaryClicked: function () {
      let that = this
      this.loading_spinner.show = true;
      this.loading_spinner.label = 'Generating Summary with Links. This may take 3-5 minutes...';

      let current_editor_contents = this.$refs.quill_editor.quill.getText()
      let current_editor_contentsHTML = this.$refs.quill_editor.quill.root.innerHTML

      this.documentModel.save(current_editor_contents, current_editor_contentsHTML, () => {
        this.documentModel.generateUserSummary(() => {
          that.loading_spinner.show = false;
          that.clearLink();
        }, () => {
          that.loading_spinner.show = false;
          alert("Please refresh this page after 5 seconds!")
          that.clearLink();
        })
      }, () => {
        that.loading_spinner.show = false;
        alert("Try Again!")
      })
    },

    //////////////////////////////////////////////////
    getLittleVersion: function(url){
      let el = document.createElement('a');
      // document.getElementById("eachArticle").setAttribute("href", url);
      // this.currentArticleLink = url;
      el.href = url;
      return el.hostname + "/..."
    },

    /////////////////////////////////////////////////
    onGenerateSectionSummaryClicked: function(heading){
      let that = this
      this.loading_spinner.show = true;
      this.loading_spinner.label = 'Generating Section Summary with Links. This may take 3-5 minutes...';

      let current_editor_contents = this.$refs.quill_editor.quill.getText()
      let current_editor_contentsHTML = this.$refs.quill_editor.quill.root.innerHTML

      this.documentModel.save(current_editor_contents, current_editor_contentsHTML,() => {
        this.documentModel.getSectionText(heading,() => {
          that.loading_spinner.show = false;
          that.clearLink();
        }, () => {
          that.loading_spinner.show = false;
          alert("Section summary failed. Try Again with unlocked articles with enough information!")
          that.clearLink();
        })
      }, () => {
        that.loading_spinner.show = false;
        alert("Save failed. Try Again!")
      })
    },

   // https://codepen.io/percipient24/pen/eEBOjG
  //
  //   breakWholeDocument: function(wholeDocument){
  //   },

    findDiff: function(actualArticle, tempWholeDoc){

        let Delta = Quill.import('delta');

        let articleSentences = new Delta();
        let allSentences = null;
        let blockDocument = this.documentModel;

        console.log("tempWholeDocument in findDiff")
        console.log(tempWholeDoc)
        if(this.studyLevel === 'no-controls'){
          allSentences = new Delta();
          let y;
          for(y = 0; y < blockDocument.sentences.length; y++){
            allSentences.insert(blockDocument.sentences[y].text + " ");
          }
        }else {
          allSentences = new Delta(tempWholeDoc);
          // allSentences = tempWholeDoc;
        }

        let i;
        for(i = 0; i < actualArticle.sentences.length; i++){
          articleSentences.insert(actualArticle.sentences[i].text);
        }

        let diff = allSentences.diff(articleSentences);
        console.log('article', articleSentences);
        console.log('all', allSentences);
        console.log('diff', diff);
        for (let i = 0; i < diff.ops.length; i++) {
          let op = diff.ops[i];
          // if the change was an insertion
          if (op.hasOwnProperty('insert')) {
            // color it green
            /*op.attributes = {
              background: "#cce8cc",
              color: "#003700"
            };*/
          }
          //if no change
          if (op.hasOwnProperty('retain')) {
            // color it pink
            op.attributes = {
              background: "#FFC0CB",
              color: "#370000"
            };
          }
          // if the change was a deletion
          if (op.hasOwnProperty('delete')) {
            // keep the text
            op.retain = op.delete;
            delete op.delete;
            // but color it red and struckthrough
            // op.attributes = {
            //   background: "#e8cccc",
            //   color: "#370000",
            //   strike: true
            // };
          }
        }
        // console.log('diff', diff);

        let adjusted = allSentences.compose(diff);
        // // console.log('adjusted', adjusted);
        //
        return adjusted
        // // profit!
        // quill_diff.setContents(adjusted);
    },

    getSectionSentences: function(wholeDocDelta, actualSectionArticle, sectionInfo){
      let Delta = Quill.import('delta');
      let oneArray = []
      let sectionArraySentences = []
      let lastArray = []
      let tempArray = []
      //let reachedSection = false
      for (let i = 0; i < wholeDocDelta.ops.length; i++) {
        let op = wholeDocDelta.ops[i];
        // if the change was an insertion
        if (op.hasOwnProperty('insert')) {
          if (op.insert == sectionInfo.heading){
            if (op.hasOwnProperty('attributes')){
              if(op.attributes.hasOwnProperty('bold')){
                if(op.attributes.bold == true){
                  oneArray.push(op)
                  tempArray = wholeDocDelta.ops.slice(i+1, wholeDocDelta.ops.length)
                  console.log("tempArray")
                  console.log(tempArray)
                  break
                }else{
                  oneArray.push(op)
                }
              }else{
                oneArray.push(op)
              }
            }else{
              oneArray.push(op)
            }
          }else{
            oneArray.push(op)
          }
        }else{
          oneArray.push(op)
        }
      }
      console.log("oneArray")
      console.log(oneArray)
      // let reachedNextSection = false
      for (let j = 0; j < tempArray.length; j++) {
        let singleTemp = tempArray[j];
        if (singleTemp.hasOwnProperty('insert')) {
            if (singleTemp.hasOwnProperty('attributes')){
              if(singleTemp.attributes.hasOwnProperty('bold')){
                if(singleTemp.attributes.bold == true){
                  lastArray = tempArray.slice(j, tempArray.length)
                  break
                }else{
                  sectionArraySentences.push(singleTemp)
                }
              }else{
                sectionArraySentences.push(singleTemp)
              }
            }else{
              sectionArraySentences.push(singleTemp)
            }
          }else{
          sectionArraySentences.push(singleTemp)
          }
        }
      console.log("all sectionArraySentences")
      console.log(sectionArraySentences)

      console.log("lastArray")
      console.log(lastArray)

      // let allSectionSentencesEditor = new Delta({ops: sectionArraySentences})
      let allSectionSentencesEditor = new Delta(sectionArraySentences)
      let sectionArticleSentences = new Delta()
      let k;
      for(k = 0; k < actualSectionArticle.sentences.length; k++){
        sectionArticleSentences.insert(actualSectionArticle.sentences[k].text);
      }

      let diff = allSectionSentencesEditor.diff(sectionArticleSentences);
      console.log('articleSection', sectionArticleSentences);
      console.log('allSection', allSectionSentencesEditor);
      console.log('diffSection', diff);
      for (let x = 0; x < diff.ops.length; x++) {
        let op = diff.ops[x];
        // if the change was an insertion
        if (op.hasOwnProperty('insert')) {
          // color it green
          /*op.attributes = {
            background: "#cce8cc",
            color: "#003700"
          };*/
        }
        //if no change
        if (op.hasOwnProperty('retain')) {
          // color it pink
          op.attributes = {
            background: "#FFC0CB",
            color: "#370000"
          };
        }
        // if the change was a deletion
        if (op.hasOwnProperty('delete')) {
          // keep the text
          op.retain = op.delete;
          delete op.delete;
          // but color it red and struckthrough
          // op.attributes = {
          //   background: "#e8cccc",
          //   color: "#370000",
          //   strike: true
          // };
        }
      }
      console.log('diff', diff);
      let oneArrayDelta = new Delta(oneArray);
      let sectionSentencesAdjusted = allSectionSentencesEditor.compose(diff)
      let lastArrayDelta = new Delta(lastArray);

      let adjusted1 = oneArrayDelta.concat(sectionSentencesAdjusted)
      let fullyAdjusted = adjusted1.concat(lastArrayDelta)
      // let adjusted = allSentences.compose(diff);
      // // console.log('adjusted', adjusted);
      //
      return fullyAdjusted
      // // profit!
      // quill_diff.setContents(adjusted);

    },

    //
    turnOnArticleSentences: function(actualArticle, section=null){
      if(this.showArticleSentencesTempObj !== null){
        this.turnOffArticleSentences();
      }
      console.log(this)
      //store current document state before highlighting article sentences
      if(this.studyLevel=='no-controls'){
        this.tempWholeDocument = null
      }
      else {
        this.tempWholeDocument = this.$refs.quill_editor.quill.getContents(); // this should return a delta object
      }
      console.log("this.tempWholeDocument in turnOn")
      console.log(this.tempWholeDocument)
      if(section == null) {
        this.$refs.quill_editor.quill.setContents(this.findDiff(actualArticle, this.tempWholeDocument));
      }else{
        this.$refs.quill_editor.quill.setContents
                                      (this.getSectionSentences(this.tempWholeDocument, actualArticle, section))
      }
      this.showArticleSentencesTempObj = actualArticle.id;
    },

  //
    turnOffArticleSentences: function (){
      let Delta = Quill.import('delta');
      let documentSentences = new Delta();
      if(this.studyLevel === 'no-controls'){
        // this assumes tempWholeDocument is null, since no user edits updates the editor
        let y;
        for(y = 0; y < this.documentModel.sentences.length; y++){
          documentSentences.insert(this.documentModel.sentences[y].text + " ");
        }
      }
      this.$refs.quill_editor.quill.setContents(this.studyLevel === 'no-controls'
          ? documentSentences:this.tempWholeDocument);

      // this.$refs.quill_editor.quill.setContents(this.tempWholeDocument);
      this.showArticleSentencesTempObj = null;

    },



    decideTurnOnTurnOff: function(actualArticleLink){
      // if(tur)

    }

  }
};
</script>

<!--<style lang="scss">-->
<!--@import "../../node_modules/@voerro/vue-tagsinput/dist/style.css";-->
<!--</style>-->

<style>
#quill_editor .ql-editor {
  min-height: 500px;
}

/*#quill_editorNo {*/
/*  min-height: 500px;*/
/*}*/

p {
  margin: 0;
}

ul { margin: 0; }

/*a:hover {*/
/*  color: blue;*/
/*  border-style: dotted;*/
/*}*/

/*.ql-save:after {*/
/*  content: "Save";*/

/*}*/

/*.ql-addLink:after {*/
/*  content: "+Link";*/
/*}*/

/*.ql-showLinks:after {*/
/*  content: "SL";*/
/*}*/

/*.ql-generateSummary:after {*/
/*  content: "GS";*/
/*}*/


/*.line-dotted:hover {*/
/*  border-style: dotted;*/
/*}*/

/*.line-dotted2:hover {*/
/*  border-style: dotted;*/
/*}*/

/*.line-solid {*/
/*  border-style: solid;*/
/*}*/

/*.line-double {*/
/*  border-style: double;*/
/*}*/
</style>
