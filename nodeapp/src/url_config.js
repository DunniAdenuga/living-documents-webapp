let urlConfig = {};

//urlConfig.base_url = 'http://192.168.99.100:9080/documents/'
//urlConfig.base_url = 'http://lws-hanrahan.ist.psu.edu:9080/documents/';

//urlConfig.base_url = 'http://130.203.136.198:8000/documents/';
//urlConfig.base_url = 'http://living-documents.ist.psu.edu/documents/';
urlConfig.base_url = 'http://living-documents.ist.psu.edu:8000/documents/';
//urlConfig.base_url = 'http://localhost:8000/documents/';
let summarizers = ["textrank", "fast", "frequency", "presum","bart", "t5", "gpt3"]
// you can only run this once at a time because ui is coupled with server in one docker container
urlConfig.summarizer_url = urlConfig.base_url + summarizers[6] + '/';

let testingBoolean = true;
urlConfig.testing = testingBoolean;

let studyLevels = ['all-controls', 'some-controls', 'no-controls'];
urlConfig.studyLevel = studyLevels[0];

module.exports = urlConfig;
