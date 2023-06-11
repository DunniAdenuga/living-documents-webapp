import axios from 'axios';
import qs from 'qs';
let urlConfig = require('../url_config')


/**
 * This handles a lot of formatting and changing the underlying document
 */
export default class DocumentModel {
  constructor () {
    this.summarizer_url = urlConfig.summarizer_url;
    this.base_url = urlConfig.base_url;
    this.id = '';
    this.title = '';
    this.author = 'no_auth'; // author is unused at the moment
    this.sentences = [];
    this.sections = [];
    this.keywords = [];
    this.articles = [];
    this.suggested_links= [];
    this.documentHistories= [];
  }

  /**
   * This is the getter that vue editor binds to later on
   * @returns {string} the rendered text of the actual document
   */
  get text () {
    let text = '';
    // let sentence_urls = this.getUrls()
    // console.log(this.sentences)
    // console.log(this.articles)

    // this is the introduction paragraph with no section
    for (let sentence of this.sentences) {
      if (sentence !== ' ') {
        text = text + ' ' + sentence.text;
      }
    }
    // remove initial space that gets added to first sentence as a result of concatenation
    text = text.trimStart()

    for (let section of this.sections) {
      // do the heading
      text = text + `\n\n<b>${section.heading}</b>\n`;
      // and the sentences for that section
      if (section.sentences.length != 0) {
        for (let sentenceSection of section.sentences) {
          text = text + ' ' + sentenceSection.text;
        }
      }
    }

    return text;
  }

  /**
   * It complains if you don't have these, but I don't really need them the way I do stuff
   * @param value
   */
  set text (value) { }

  load (id) {
    // let uri = this.base_url + `${id}/`;
    let uri = urlConfig.base_url + `${id}/`;

    return axios.get(uri).then((response) => {
      this.deserialize(response.data);
    }).catch(function (error) {
      alert("Try Again. \n Error: " + error.message);
    });
  }

  checkIfSectionExists(htmlText){
    let searchPhrase = '';
    let hasBoldText = false;

    if (htmlText.includes("<strong>") && htmlText.includes("</strong>")){
      searchPhrase = 'strong>';
      hasBoldText = true;
    }else if(htmlText.includes("<b>") && htmlText.includes("</b>")){
      searchPhrase = 'b>';
      hasBoldText = true;
    }
    let parts = []
    if(hasBoldText){
      parts = htmlText.split(searchPhrase)
    }else{
      parts[0] = htmlText
    }

    console.log("divide html per bold")
    console.log(hasBoldText, parts)
    let results = {"hasBoldText": hasBoldText, "parts": parts}
    return results;
  }

  removeHtmlTags(editor_text){
    let domParser = new DOMParser()
    let doc = domParser.parseFromString(editor_text, 'text/html')
    return doc.body.textContent
  }

  updateSentences(params, sectionIndex, actualEditorContentsJsonObject, isLastSection){
    let old_sentences = []
    if(sectionIndex < 0){
      old_sentences = this.sentences
    }else{
      old_sentences = this.sections[sectionIndex].sentences
    }
     // sentences from generating summary before user made editions
    let old_sentences_text = []
    for (let old_sent of old_sentences) {
      old_sentences_text.push(old_sent.text); //textual version of above
    }
    console.log("old-sentences-text" + sectionIndex)
    console.log(old_sentences_text)

    let jsonKey = Object.keys(actualEditorContentsJsonObject)[0]
    let jsonValue = actualEditorContentsJsonObject[jsonKey]
    let editor_text = ""

    if((sectionIndex<0) || ((sectionIndex>=0) && (!isLastSection))){
      // introduction
      // editor_text = jsonValue.substring(3, jsonValue.length-8) //remove <p> from start, </p><p>< from end
      editor_text = this.removeHtmlTags(jsonValue).replace("<", "") //remove <p> from start, </p><p>< from end
    }else {
      if (isLastSection) {
        // last section
        // editor_text = jsonValue.substring(7, jsonValue.length - 4) //remove </p><p> from start, </p> from end
        editor_text = this.removeHtmlTags(jsonValue)
       }
        // else {
      //   //normal section
      //   // editor_text = jsonValue.substring(7, jsonValue.length - 8) //remove </p><p> from start, </p><p>< from end
      //   editor_text = this.removeHtmlTags(jsonValue).replace("<", "")
      // }
    }
    console.log("editor_text")
    console.log(editor_text)

    let new_sentences = [] //current sentences in the quill editor
    // let new_sentences_text = editor_text.replace("\n", "")
    //     .replace(/([.?!])\s+(?=[A-Z0-9])/g, "$1|").split("|")
    let possibleNewline = editor_text.substring(editor_text.length-2)
    if(possibleNewline == '\n'){
      editor_text = editor_text.substring(0, editor_text.lastIndexOf("\n"))
    }
    let new_sentences_text = editor_text.replace(/([.?!])\s+(?=[A-Z0-9])/g, "$1|").split("|")
      //quill adds new line to end of text so, i remove it above
    console.log("new-sentences-text")
    console.log(new_sentences_text)

    //if old sentences are in the "new" quill editor contents, keep the already created
    // sentence json object
    let position = 0
    for (let new_sent of new_sentences_text) {
      if (old_sentences_text.includes(new_sent)) {
        let index  = old_sentences_text.indexOf(new_sent)
        let new_sentence_json = old_sentences.slice(index, index+1)[0]
        new_sentence_json.position = position
        new_sentences.push(new_sentence_json)
      } else {
        new_sentences.push({
          text: new_sent, position: position,
          is_user_defined: true, is_deleted: false
        })
      }
      position = position+1
    }

      if(sectionIndex<0){
        /*1. */params.sentences = new_sentences
      }else{
        params.sections[sectionIndex].sentences = new_sentences
      }

      return params
  }


  removeArticleSentences(params, sectionIndex){
    // remove from the articles the old sentences that have been updated or deleted
    // so, they can be deleted on the backend too (hopefully)

    // Keep track of the sentences being sent to the backend
    let tempParams = null;
    // let overallTempParams = null
    let returnSection = false
    if(sectionIndex < 0){
      tempParams = params
    }else{
      console.log("section's tempParams")
      tempParams = params.sections[sectionIndex]
      returnSection = true
    }

    let new_sent_ids = []
    for (let param_sent of tempParams.sentences){
      if(param_sent.hasOwnProperty("id")){
        new_sent_ids.push(param_sent.id)
      }
    }
    // Update each article in params.articles
    let article_index = 0
    for (let article of tempParams.articles) {
      let indexes_sent_ids_to_delete_from_article = []
      let temp_index = 0
      // Update the sentence array for each article
      for (let article_sentence of article.sentences) {
        if(!new_sent_ids.includes(article_sentence.id)){
          //if current article sentence is not in sentences being sent to backend, add index of article sentence
          indexes_sent_ids_to_delete_from_article.push(temp_index)
        }
        else{
          let sent_id_to_change = tempParams.sentences
              .findIndex((element)=>element.id == article_sentence.id)
          /*2. */ tempParams.articles[article_index].sentences[temp_index].position
              = tempParams.sentences[sent_id_to_change].position
        }
        temp_index = temp_index+1
      }//end for each article sentence
      for (let i = 0; i < indexes_sent_ids_to_delete_from_article.length; i++){
        // now, remove from article sentences not in
        /*3. */  article.sentences.splice(indexes_sent_ids_to_delete_from_article[i],1)
      }
      article_index = article_index + 1;
    }//end for each article
    if(returnSection){
      params.sections[sectionIndex] = tempParams
      return params
    }else{
      return tempParams
    }
  }

  findSectionIndex(section_name){
    for(let i = 0; i < this.sections.length; i++){
      if(this.sections[i].heading == section_name){
        return i
      }
    }
    return -1
  }

  save (editor_text, editorTextHTML, onSuccess = null, onFailure = null) {
    let url = urlConfig.base_url + this.id + '/';
    let config = { headers: { 'Content-Type': 'application/json'}};
    let params = this.serialize();
    console.log("initial params")
    console.log(params)

    if(editor_text != ''){
      console.log("this.checkIfSectionExists(editorTextHTML)")
      let results = this.checkIfSectionExists(editorTextHTML)
      let hasSections = results["hasBoldText"]
      let parts = results["parts"]

      console.log("hasSections in save")
      console.log(hasSections)
      console.log("parts in save")
      console.log(parts)
      let editorContentsJson = []
      editorContentsJson.push({"Introduction</": parts[0]})
      if(hasSections){
        console.log("in here")
        for(let index=1; index<parts.length; index=index+2){
          editorContentsJson.push({[parts[index]]: parts[index+1]})
        }
      }
      console.log("editorContentsJson")
      console.log(editorContentsJson)

      for(let i = 0; i< editorContentsJson.length; i++){
        //update sentences
        let actualJson = editorContentsJson[i]
        let actualJsonKey = Object.keys(actualJson)[0]
        //check parts[index], trim
        let section_name = actualJsonKey.substring(0, actualJsonKey.length-2) //(remove > from start) NOT anymore, </ on end
        if(section_name == "Introduction"){
          params = this.updateSentences(params, -50, actualJson, false)
          params = this.removeArticleSentences(params, -50)
        }else{
          let sectionIndex = -200
          //find sectionIndex then,
          sectionIndex = this.findSectionIndex(section_name)
          console.log("sectionIndex")
          console.log(sectionIndex)
          if(sectionIndex >= 0){
            if(i == editorContentsJson.length-1){
              params = this.updateSentences(params, sectionIndex, actualJson, true)
            }else{
              params = this.updateSentences(params, sectionIndex, actualJson, false)
            }
            // params.sections[sectionIndex] = this.removeArticleSentences(params,sectionIndex)
            params = this.removeArticleSentences(params,sectionIndex)
          }
        }
        //update article sentences
      }
    }

    console.log("final params")
    console.log(params)

    axios.put(url, params, config)
      .then(() => {
        if (onSuccess !== null) {
          onSuccess();
        }
      })
      .catch((error) => {
        if (onFailure !== null) {
          onFailure();
        }
        console.log("in save method");
        console.log(error);
      });
  }

  generateUserSummary (onSuccess = null, onFailure = null) {
    let url = urlConfig.summarizer_url + this.id + '/user_summary/';
    const config = { headers: {'Content-Type': 'application/json'} };

    axios.get(url)
      .then((response) => {
        this.deserialize(response.data);
        if (onSuccess !== null) {
          onSuccess();
        }
      })
      .catch((error) => {
        if (onFailure !== null) {
          onFailure();
        }
        console.log("in generateUserSummary method");
        console.log(error);
      });
  }

  /**
   * Adds a section to the end of the document, does not save it
   * @param onSuccess
   */
  getSectionText (heading, onSuccess = null, onFailure=null) {
    let url = urlConfig.summarizer_url + this.id + '/section_summary/'
    let param = {
      section_heading: heading
    }
    axios.post(url, param).then((response) => {
      // console.log('sectionPostResponse: ');
      // console.log(response);
      this.deserialize(response.data);
      if (onSuccess !== null) {
        onSuccess();
      }
    }).catch((error) => {
      if (onFailure !== null) {
        onFailure();
      }
      console.log("in getSectionText method");
      console.log(error);
    });
  }

  modifySummaryWords(old_word, new_word, onSuccess = null) {
    let url = this.base_url + `${this.id}/change_word/`;
    let param = {
      old_word: old_word,
      new_word: new_word
    };
    axios.post(url, param).then((response) => {
      this.deserialize(response.data);

      if (onSuccess !== null) {
        onSuccess();
      }
    }).catch((error) => {
      console.log(error);
    });
  }

  serialize () {
    return {
      id: this.id,
      title: this.title,
      author: this.author,
      sections: this.sections,
      sentences: this.sentences,
      keywords: this.keywords,
      articles: this.articles,
      suggested_links: this.suggested_links,
      documentHistories: this.documentHistories
    };
  }

  deserialize (data) {
    console.log("document")
    console.log(data)
    this.id = data.id;
    this.title = data.title;
    this.author = data.author;
    this.sentences = data.sentences;
    this.sections = data.sections;
    this.keywords = data.keywords;
    this.articles = data.articles;
    this.suggested_links = data.suggested_links;
    this.documentHistories = data.documentHistories;
  }

  deleteMultipleSentences(size, i) {
    let current_sentence_index = i;
    let local_size = size;
    let sentence = this.sentences[i];
    /*TODO Do I want to update positions here*/
    while ((current_sentence_index < this.sentences.length) && (local_size > sentence.text.length)) {

      local_size = local_size - sentence.text.length;
      sentence.is_user_defined = true;
      sentence.is_deleted = true; // has no effect in the backend so, i set sentence to empty
      console.log(`Deleted Sentence?: ${sentence.text}`)
      sentence.text = ''

      current_sentence_index++;
      sentence = this.sentences[current_sentence_index];
    }
    return current_sentence_index;
  }

  trackDeletion (position, size) {
    // initialize the sentenceStart to 0, since we are at the start of the document
    let sentenceStart = 0;
    let i = 0; // loop variable
    let sentence = this.sentences[0];
    // TODO this must be tested more, I don't think I have caught all of the edge cases
    // loop through the intro sentences to find if the change is within any of those
    //for (let sentence of this.sentences) {
    while(i < this.sentences.length){

      let sentenceEnd = sentenceStart + sentence.text.length;
      // check if multiple sentences first - position should equal first of multiple sentences
      if ((position == sentenceStart) && (size >= sentence.text.length)) {
        console.log("Deleting Multiple Sentences")
        i = this.deleteMultipleSentences(size, i)
        break; /*Operation is done! multiple sentences deleted at once*/
      } else  if (position >= sentenceStart && position < sentenceEnd && size < sentence.text.length) {
        // find the end of the current sentence

        // is the starting position of the edit within these boundaries
        // TODO check if the first and last chars of a sentence are taken into account here (especially the period and the first space of the sentence)


        // need to find the position to actually delete it in this sentence
        let localPosition = position - sentenceStart;
        // the user touched this sentence, so we need to mark it as user defined
        sentence.is_user_defined = true;

        if (position < sentenceEnd) /* this is already satisfied at the top*/ {
          // CASE 1: The deletion only spans the current sentence
          // and modify the underlying sentence
          sentence.text = sentence.text.slice(0, localPosition - 1) + sentence.text.slice(localPosition - 1 + size);
          console.log(`Edited sentence should be this?: ${sentence.text}`);
        }
        break;
        // add one because of the space between sentences
      }else{
        i = i+1
        sentenceStart = sentenceEnd + 1;
      }
      sentence = this.sentences[i];
    }

    // TODO there may be a case when the deletion spans multiple sentences, highlight and delete for example across sentences this isn't handled yet
    // TODO need to mark entire sentences as deleted as well if they span multiple sentences...will have to check the end of the size to see if I actually deleted it
    // TODO don't handle any of the sections yet, this also needs to be done
  }


  //onTextChange will work properly if people are copying and pasting whole sentences
  //TODO: Update when url is removed from Sentence Serializer

  trackInsertion (position, insertedContent, oldContent) {
    console.log(position)
    console.log(insertedContent)
    console.log(oldContent)

    console.log("document sentences")
    console.log(this.sentences)

    if (insertedContent != "" ||  insertedContent != " ") {
      if (insertedContent.split(" ").length > 1) { // sentence was inserted (more than one word)
        let current_length = 0
        let i = -1
        while ((current_length <= position) && (i+1 < this.sentences.length)){
          current_length = current_length + this.sentences[i+1].text.length + 1
          i = i + 1
        }
        console.log("current length")
        console.log(current_length)

        console.log("i")
        console.log(i)

        if ((i+1 >= this.sentences.length) && (position > current_length)){ // sentence was inserted in section
          // go to sections
          this.trackInsertionSection(position, current_length, insertedContent)

        } else {
          //insert after the current i

          let new_sentences = this.sentences.slice(0, i+1)
          let x = i
          for (let insertedSentence of insertedContent.split(".")) {
            new_sentences.push({
              text: insertedSentence, position: x, url: '',
              is_user_defined: true, is_deleted: false
            })
            // x = x+1
          }
          new_sentences = new_sentences.concat(this.sentences.slice(i+1))
          this.sentences = new_sentences

          console.log("new document sentences")
          console.log(this.sentences)
        }
      }
    }
  }

  trackInsertionSection(position, currentLength, insertedContent){
    console.log("in track section sentences")

    let section_current_length = currentLength

    for (let section of this.sections){
      section_current_length = section_current_length + section.heading.length + 1
      let i = -1

      while ((section_current_length < position) && (i+1 < section.sentences.length)){
        section_current_length = section_current_length + section.sentences[i+1].text.length + 1
        i = i + 1
      }
      if (i+1 >= section.sentences.length){
        // go to next section
      } else{
        // insert into current section
        console.log("old section sentences")
        console.log(section.sentences)

        let new_section_sentences = section.sentences.slice(0, i)
        for (let insertedSentence of insertedContent.split(".")) {
          new_section_sentences.push({
            text: insertedSentence, position: i, url: '',
            is_user_defined: true, is_deleted: false
          })
        }
        new_section_sentences = new_section_sentences.concat(section.sentences.slice(i))
        section.sentences = new_section_sentences

        console.log("new section sentences")
        console.log(section.sentences)

        return
      }

    }
  }
}
