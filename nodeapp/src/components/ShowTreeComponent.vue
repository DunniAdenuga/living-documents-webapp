<template>
  <div>
    <navigation-bar></navigation-bar>
    <b-container style="overflow: auto" fluid>
      <b-row class="justify-content-center">
        <b-col :cols= "this.showJumbotron? '3': '12'">
          <b-button size="sm"
                    class="mt-3 mx-5"
                    variant="success"
                    @click="goBack">
            Go back to Document
          </b-button>
          <b-button size="sm"
                    class="mt-3 mx-5"
                    variant="success"
                    @click="treeShow">
            {{ this.showTree ? "Hide Concept Graph":"Show Concept Graph" }}
          </b-button>
          <b-button size="sm"
                    class="mt-3 mx-5"
                    variant="success"
                    @click="jumbotronShow">
            {{ this.showJumbotron ? "Hide Quick Info":"Show Quick Info" }}
          </b-button>
        </b-col>
        <b-col cols="9" v-if="showJumbotron">
          <b-jumbotron class="mt-1 mx-2" lead="Quick Info">
            <li>The Concept Graph represents the document in graphical form and has nodes and links</li>
            <li>Nodes represent important words that make up the document. Click the node to view how the nodes are represented in the summmary</li>
            <li>Links(lines between nodes) show how the words/nodes are connected in the document</li>
          </b-jumbotron>
        </b-col>
      </b-row>

      <b-row>
        <b-col cols="4">
          <b-alert v-model="showNodeDismissibleAlert" style="z-index: 1;" :style="{ position: 'absolute', top: mouseY + 'px', left: mouseX + 'px' }"
                   variant="info" dismissible>
            <h5 style="text-decoration: underline;">Represented Words</h5>
            <p>{{"\n"}}</p>
            <p>{{ alertedNodeInformation }}</p>
          </b-alert>
<!--          <b-jumbotron v-show="showNodeDismissibleAlert" :style="{ position: 'absolute',-->
<!--        width: '100px', height: '100px', top: mouseY + 'px', left: mouseX + 'px' }">-->
<!--            <u><h6>Represented Words</h6></u>-->
<!--            <p>{{ alertedNodeInformation }}</p>-->
<!--          </b-jumbotron>-->
        </b-col>
      </b-row>

      <div v-if="showTree" style="width: 100%; height: 100%; overflow: auto">
        <d3-network :net-nodes="nodes" :net-links="links" :options="options" @node-click="showNodeDetails"/>
      </div>

<!--      <div v-if="showTree" style="width: 100%; height: 100%; overflow: auto">-->
<!--        <d3-network :net-nodes="nodes" :net-links="links"-->
<!--                    :options="options" @node-click="showNodeDetails"/>-->
<!--      </div>-->
    </b-container>
  </div>
</template>

<script>
  import axios from 'axios'
  import {tree} from 'vued3tree'
  import D3Network from 'vue-d3-network'
  import NavigationBar from './NavigationBar';
  let urlConfig = require('../url_config');

  export default {
        name: "ShowTreeComponent",

        components: {
          NavigationBar,
          tree,
          D3Network
        },

        data() {
          return {
            showJumbotron: true,
            stopwords: ['i','me','my','myself','we','our','ours','ourselves','you','your','yours','yourself',
              'yourselves','he','him','his','himself','she','her','hers','herself','it','its','itself','they','them',
              'their','theirs','themselves','what','which','who','whom','this','that','these','those','am','is','are',
              'was','were','be','been','being','have','has','had','having','do','does','did','doing','a','an','the',
              'and','but','if','or','because','as','until','while','of','at','by','for','with','about','against',
              'between','into','through','during','before','after','above','below','to','from','up','down','in','out',
              'on','off','over','under','again','further','then','once','here','there','when','where','why','how','all',
              'any','both','each','few','more','most','other','some','such','no','nor','not','only','own','same','so',
              'than','too','very','s','t','can','will','just','don','should','now'],
            num_roots: 0,
            treeData: {name: 'Triple Graph', children:[]},
            document_id: -1,
            showTree: false,
            base_url: '',

            backendTreeDataArray: [],
            idNodeHelper: 0,
            listOfNodesHelper: [],

            nodes: [],
            links: [],
            options:
              {
                force: 1700,
                nodeSize: 10,
                nodeLabels: true,
                linkWidth:4,
                canvas: false,
                size: {w:1200, h:1200}
              },
            //label: 'Show Tree'
            alertedNodeInformation: "",
            showNodeDismissibleAlert: false,
            tempAllNodesInformation: [],

            mouseX: 0, // X-coordinate of mouse position
            mouseY: 0, // Y-coordinate of mouse position

            currentPressedNode: {"id": -345, "name": ""}
          }
        },

        methods: {
          goBack: function(){
            this.document_id = this.$route.params.id
            let self = this
            this.$router.push({
              name: 'userEdit',
              params: {id: self.document_id}
            })
          },

          treeShow: function(){
            // let that = this
            if(this.showTree == false){
              this.getTreeData()
            }
            else {
              this.showTree = false
              this.showJumbotron = true
              this.showNodeDismissibleAlert = false
            }
          },

          jumbotronShow: function () {
            this.showJumbotron = !this.showJumbotron
          },

          getTreeData: function(){
            this.showJumbotron = false;
            // let url = this.url_heading + `${this.id}/get_tree/`
            this.document_id = this.$route.params.id
            this.base_url = urlConfig.base_url;

            let url = this.base_url + `${this.document_id}/get_tree/`;
            axios.get(url).then((response) => {
              console.log("response.data")
              console.log(response.data)
              console.log("response.data.graph_str")
              console.log(response.data.graph_string_version)
              this.treeData.children = response.data.doc_graph
              this.backendTreeDataArray = response.data.doc_graph
              this.createNodes(this.backendTreeDataArray)

              console.log(this.treeData)
              console.log("Created Nodes")
              console.log(this.nodes)
              console.log("Created Links")
              console.log(this.links)
              this.showTree = true
            })
          },

          createNodes: function(doc_graph){
                let graph_length = doc_graph.length;
                for(let x=0; x< graph_length; x++){
                  this.createNodesHelper(doc_graph[x])
                }
          this.createLinks(doc_graph);
          },

          createNodesHelper: function(eachNode){
            if (!this.listOfNodesHelper.includes(eachNode.name)) {
              this.idNodeHelper = this.idNodeHelper + 1;

              let wordsArray = eachNode.name.split("\n")
              let newNode = {};
              if(this.stopwords.includes(wordsArray[0])){
                let root_name = "CONNECTOR--" + this.num_roots;
                newNode = {id: this.idNodeHelper, name: root_name};
                this.num_roots++;
              }else{
                newNode = {id: this.idNodeHelper, name: wordsArray[0]};
              }
              this.nodes.push(newNode);

              let tempNewNode = {id: this.idNodeHelper,
                fullWords: eachNode.name, actualWords: wordsArray[1].split(": ")[1]}
              this.tempAllNodesInformation.push(tempNewNode);

              this.listOfNodesHelper.push(eachNode.name);
            }
            if(eachNode.children.length != 0) {
                for (let eachNodeChild of eachNode.children){
                  this.createNodesHelper(eachNodeChild);
                }
            }
            else{
              return
            }
          },

          createLinks: function(doc_graph){
            let graph_length = doc_graph.length;
            for(let x=0; x< graph_length; x++){
              this.createLinksHelper(doc_graph[x])
            }
          },

          createLinksHelper: function(eachNode){
            if(eachNode.children.length != 0) {
              let sourceId = this.listOfNodesHelper.indexOf(eachNode.name) + 1
              for (let eachNodeChild of eachNode.children){
                let targetId = this.listOfNodesHelper.indexOf(eachNodeChild.name) + 1
                let newLink = {sid: sourceId, tid: targetId};
                this.links.push(newLink);
                this.createLinksHelper(eachNodeChild);
              }
            }
            else{
              return
            }
          },

          // updateMousePosition: function(event){
          //   this.mouseX = event.pageX;
          //   this.mouseY = event.pageY;
          // },

          showNodeDetails: function(event, node_object){
              if(this.showNodeDismissibleAlert && (this.currentPressedNode.id == node_object.id)){
                this.showNodeDismissibleAlert = false
              }else{
                this.mouseX = event.screenX;
                this.mouseY = event.screenY;
                this.showNodeDismissibleAlert = true
                let node_name = this.tempAllNodesInformation.find(({ id }) => id === node_object["id"])["actualWords"]
                this.alertedNodeInformation = "\n\n" + node_name;
                this.currentPressedNode = {"id": node_object.id, "name": node_object.name};
              }
            }
        },

    }
</script>

<style src="vue-d3-network/dist/vue-d3-network.css"></style>


<style scoped>

</style>
