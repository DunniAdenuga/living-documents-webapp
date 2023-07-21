from typing import List, Dict, Any

from pycorenlp import StanfordCoreNLP
import logging, datetime

from text_generation.models.sentence import Sentence
from text_generation.models.triple import Triple
from text_generation.utilities import process_text

from living_documents_server.settings import NLP_SERVER_URL


RELATION = 'RELATION'
OBJECT = 'OBJECT'

logger = logging.getLogger(__name__)


class Node:
    """This is the node that is used to construct the TripleGraph, each node has three types of children
        subjects, objects, relations. Use the RELATION, OBJECT global variables to specify which
        type of child your are adding.
    """

    # all of the sentences that this token has been involved in

    def __init__(self, token: str, speech_type: str, sentence, first_actual_word):
        """
        :param str token: the token/stemmed word dict that the node represents
        :param str speech_type: the type of speech that the node is (use RELATION, or OBJECT global variables)
        :param Sentence sentence: the sentence that this token came from
        """
        self.token = token
        self.sentences = set()
        self.actual_words_b4_stemmer = set()
        self.sentences.add(sentence)
        self.actual_words_b4_stemmer.add(first_actual_word)
        # use the RELATION, or OBJECT global variables
        self.speech_type = speech_type
        # child dictionary with edges as values and nodes as keys
        self.children = {}
        self.color = 0

    def __hash__(self):
        """Don't want the memory location in this"""
        return hash((self.token, self.speech_type))

    def __eq__(self, other):
        """Don't want the memory location in this"""
        return (self.token, self.speech_type) == (other.token,
                                                  other.speech_type)

    def __ne__(self, other):
        """Don't want the memory location in this"""
        return (self.token, self.speech_type) != (other.token,
                                                  other.speech_type)

    def __str__(self) -> str:
        return self.token.format() + "\nActual words: " + ', '.join(str(s) for s in self.actual_words_b4_stemmer)
        # return str(self.token)
        # return f'{self.token}'

    def add_child(self, child: 'Node') -> 'Node':
        """This function adds a child with a of speech_type key (specified by RELATION, and
         OBJECT global variables) or, if the child/type already exists increments the weight of the edge

        :param Node child: the node to add
        :return: the Node that is in the actually in the tree
        """
        if child in self.children:
            self.children[child] += 1
            tree_node = self.get_child(child)
            tree_node.sentences.update(child.sentences)
            tree_node.actual_words_b4_stemmer.update(child.actual_words_b4_stemmer)
            return tree_node
        else:
            self.children[child] = 1
            return child

    def delete_sentence(self, del_sentence) -> 'bool':
        if del_sentence in self.sentences:
            self.sentences.remove(del_sentence)
            # remove sentence
            # Sentence.objects.get(pk=del_sentence.id).delete()
        if len(self.sentences) > 0:
            return True
        return False

    def delete_actualWord(self, del_actualWord) -> 'bool':
        if del_actualWord in self.actual_words_b4_stemmer:
            self.actual_words_b4_stemmer.remove(del_actualWord)
        if len(self.actual_words_b4_stemmer) > 0:
            # I guess if node is still valid by having content
            return True
        return False

    def delete_child(self, child: 'Node', child_sentence) -> 'bool':
        if self.is_child_sentence(child, child_sentence):
            if self.children[child] > 1:
                self.children[child] -= 1
                return False
            else:
                self.children.pop(child)
                return True
        raise ValueError("child not exists")

    def is_child_sentence(self, child: 'Node', child_sentence) -> bool:
        if child in self.children:
            tree_node = self.get_child(child)
            if child_sentence in tree_node.sentences:
                return True
        return False

    def is_child_actualWord(self, child: 'Node', child_actualWord) -> bool:
        if child in self.children:
            tree_node = self.get_child(child)
            if child_actualWord in tree_node.actual_words_b4_stemmer:
                return True
        return False

    def get_child(self, item: 'Node') -> 'Node':
        """Gets the node that is in the graph that matches the name/pos of the node you are looking for (item)

        :param Node item: the node with the values you are looking for
        :return: the node in the graph or None if it isn't in the tree
        """
        child_nodes = list(self.children.keys())
        # filter the collection and return it
        matching = list(filter(lambda x: x == item, child_nodes))
        if matching:
            return matching[0]
        else:
            return None

    def merge(self, node: 'Node') -> 'Node':
        """Takes a similar node and merges it with the one in the tree

        :param Node node:
        :return Node: the merged node in the tree
        """
        # merge the children, which merges sentences
        self.sentences.update(node.sentences)
        self.actual_words_b4_stemmer.update(node.actual_words_b4_stemmer)
        for child in node.children:
            self.add_child(child)

        return self

    ######################


class _NetworkXNode:
    """This is a class that I have to wrap the Node in to correctly render the NetworkX graphs, it is needed because
    you can't duck punch special methods like __str__ or __hash__ which we DO want to change so that we don't merge
    relation nodes, all of which is stupid and you should be able to pass a lambda to networkX or duck punch 'special'
    methods, don't use this class or modify it unless you are dealing with NetworkX"""

    def __init__(self, node: Node):
        self.node = node
        self.children = node.children
        self.speech_type = node.speech_type

    def __str__(self):
        return self.node.token.format()
        # return f'{self.node.token}'

    def __hash__(self):
        return id(self.node)

    def __eq__(self, other):
        return id(self.node) == id(other.node)


class TripleGraph:
    """This is the graph of all of the triples sitting on the sentences"""

    def __init__(self,
                 sentences,
                 tfidf_scores: Dict = {str: float},
                 min_cut: float = 0,
                 max_cut: float = 1):
        """Initializes and builds a graph based on the sentences and their triples, the nodes that are inserted
        are filtered by their token's tfidf score via the min and max cuts.

        :param List[Sentence] sentences: Set of sentences to build a graph for, this should come from a document object
        :param Dict{str: float} tfidf_scores: The tf_idf scores for all of the tokens, this is generated by document object
        :param float min_cut: the floor to filter out nodes
        :param float max_cut: the ceiling to filter out nodes
        """
        # logger.warning("sentences before before b4")
        # logger.warning(sentences)
        self.sentences = sentences
        logger.warning("sentences before connecting")
        logger.warning(self.sentences)
        logger.warning(
            '{}: Connecting to ' + NLP_SERVER_URL + " ".format(
                datetime.datetime.now()))
        self._nlp_server = StanfordCoreNLP(NLP_SERVER_URL)
        logger.warning("after NLP server is set")
        self._min_cut = min_cut
        self._max_cut = max_cut
        self._tfidf_scores = tfidf_scores
        # self._token_lookup = {str: Node}
        self._token_lookup = []
        self._build_graph()
        self._equivalent_colors = []
        # self._update_tfidf = False

    def _build_graph(self):
        """Internal function that inserts all of the nodes for initial list of sentences"""
        self.tokens = {str: Node}
        self.roots = []
        logger.warning("in internal build-triple graph")
        # logger.warning("self.sentences")
        # logger.warning(self.sentences)
        for sentence in self.sentences:
            logger.warning("for sentence in graph sentences")
            # only build if sentence doesn't already have triples
            if len(sentence.triple_set.all()) == 0:
                logger.warning("about to build triples with each sentence")
                sentence.build_triples()
            # if it still doesn't have any triples from openie,
            # then it is probably a bogus sentence and we can delete it
            if len(sentence.triple_set.all()) == 0:
                if not sentence.is_user_defined:
                    logger.warning(f'NO TRIPLE FOUND in non-user defined sentence. DELETING: f{sentence.text}')
                    sentence.delete()
            # but if it does have a triple, then insert it
            else:
                logger.warning("in else block to insert")
                for triple in sentence.triple_set.all():
                    self.insert_triple(sentence, triple)
        logger.warning("done with internal build-triple graph")

    def insert_triple(self, sentence, triple: Triple) -> (Node, Node, Node):
        """Aside from initializing the graph, this is the only place you should be calling externally. This function
        takes a triple and sentence and inserts it into the graph, it handles all of the merging and what not inside
        this function if a new connection is made.

        :param Sentence sentence: The sentence that the triple belongs to
        :param Dict triple: The triple (generated by Document object)
        :return Node: returns the root subject node
        """
        # this should return one or no items, if it is no items then it was a stop word or something
        # and it isn't important to keep going
        # if self._update_tfidf:
        #     raise ValueError("Please update tfidf scores after delete triples!")

        # filter the subject and object by tf-idf (not relation)
        logger.warning("in insert-triple")
        processed_subject = self._process_triple_element(triple.subject)
        logger.warning("processed_subject")
        # logger.warning(processed_subject)
        processed_relation = self._process_triple_element(
            triple.relation, False, False)
        logger.warning("processed_relation")
        # logger.warning(processed_relation)
        processed_object = self._process_triple_element(triple.object)
        logger.warning("processed_object")
        # logger.warning(processed_object)
        #  if processed_subject and processed_object:

        if processed_subject and processed_object:
            subject_node = self._insert_triple_nodes(
                processed_subject, processed_relation, processed_object,
                sentence)

            return subject_node
        # if the filtering takes out the sentence, it is *probably* a bogus sentence, we could tune this if we find
        # that we are filtering too many sentences out
        else:
            logger.warning(f'DELETING THE TRIPLE:\n{triple}\n{sentence.text}')
            # wipe out the filtered triple
            triple.delete()
            # if there are no more valid triples, get rid of the sentence
            if sentence.triple_set.all().count() == 0:
                logger.warning(f'ALL TRIPLES DELETED, DELETING SENTENCE:\n{sentence.text}')
                sentence.delete()

    def update_tfidf(self, tfidf_scores):
        self._tfidf_scores = tfidf_scores
        # self._update_tfidf = False

    def delete_sentence(self, sentence):
        for triple in sentence.triple_set.all():
            self.delete_triple(sentence, triple)

    def delete_triple(self, sentence, triple: Triple):
        # self._update_tfidf = True
        processed_subject = self._process_triple_element(triple.subject)
        processed_relation = self._process_triple_element(
            triple.relation, False, False)
        processed_object = self._process_triple_element(triple.object)

        if processed_subject and processed_object:
            subject_node = self._delete_triple_nodes(
                processed_subject, processed_relation, processed_object,
                sentence)
            return subject_node

    def _delete_triple_nodes(self, subject_tokens: List[Dict],
                             relation_tokens: List[Dict],
                             object_tokens: List[Dict], sentence) -> Node:
        """This takes the tokens from the triple and deletes the appropriate nodes.

        :param List[str] subject_tokens: tokens for subject
        :param List[str] relation_tokens: tokens for relation
        :param List[str] object_tokens: tokens for object
        :param Sentence sentence: the sentence that the tokens are in
        :return Node: root subject node
        MODIFY THE TOKEN lOOKuP
        """
        popped_token = subject_tokens.pop(0)
        subject_node = Node(popped_token["stemmed_word"], OBJECT, sentence)
        ifInTokenLookUp, nodeInTokenLookUp = self.searchTokenLookUp(subject_node)
        if ifInTokenLookUp:
            subject_node = nodeInTokenLookUp
        # if subject_node in self._token_lookup:
        #     subject_node = self._token_lookup[subject_node]
        if not subject_node.delete_sentence(sentence):
            if subject_node in self._token_lookup:
                self._token_lookup.remove(subject_node)
        #         changed pop to remove
        # remove subject node from root
        if subject_node in self.roots:
            self.roots.remove(subject_node)

        current_subject = subject_node
        current_subject = self._delete_triple_children(
            current_subject, subject_tokens, OBJECT, sentence)
        # add relation tokens
        current_relation = self._delete_triple_children(
            current_subject, relation_tokens, RELATION, sentence, False)
        # add the object tokens
        self._delete_triple_children(current_relation, object_tokens, OBJECT,
                                     sentence)

        return subject_node

    def _delete_triple_children(self,
                                current_node: Node,
                                tokens: List[Dict],
                                part_of_speech: str,
                                sentence,
                                is_object: bool = True):
        """This recursively deletes the list of tokens.
        :param Node current_node: whatever the parent node should be
        :param List[str] tokens: the tokenized version of the triple element
        :param str part_of_speech: which pos the tokens belong to
        :param Sentence sentence: the sentence the tokens are part of
        :param bool is_object: switch to treat object and relation differently
        :return:
        """
        for token in tokens:
            if current_node is not None:
                # construct the token
                to_delete = Node(token["stemmed_word"], part_of_speech, sentence)
                child_node = current_node.get_child(to_delete)
                # delete the child from current subject
                if current_node.is_child_sentence(to_delete, sentence):
                    if current_node.delete_child(to_delete, sentence):
                        if not self._is_reachable(child_node):
                            self.roots.append(child_node)

                # delete sentence from child
                if child_node is not None:
                    if not child_node.delete_sentence(sentence):
                        if is_object:
                            if child_node in self._token_lookup:
                                self._token_lookup.remove(child_node)
                        # remove the child node from root candidate
                        if child_node in self.roots:
                            self.roots.remove(child_node)

                current_node = child_node

        return current_node

    def _process_triple_element(self,
                                text: str,
                                filter_stops: bool = True,
                                filter_tfidf: bool = True) -> List[str]:
        """Internal function that takes a triple element and does a number of operations including stemming and
        filtering (e.g. 'little lamb' returns two stemmed tokens).

        :param str text: the text of the triple element
        :param bool filter_stops: whether or not you want to exclude stop words (you probably don't if it is a RELATION)
        :param filter_tfidf: whether or not you want to exclude meaningless words (you probably don't if it is a RELATION)
        :return List[str]: the processed tokens from the triple
        """
        # List of Dicts {"stemmed_word": "", "processed_word": "", "actual_word": ""}
        tokens = process_text(text, filter_stops)

        def tfidf_filter_func(token):
            """ function used in filter to get rid of low/high tfidf scored words

            :param str token: the token to get rid of CHANGED cus I made token a dict
            :return bool: include the token or not
            """
            if token["stemmed_word"] in self._tfidf_scores:
                return self._max_cut >= self._tfidf_scores[token["stemmed_word"]] >= self._min_cut, tokens
            else:
                return False

        if filter_tfidf:
            tokens = list(filter(tfidf_filter_func, tokens))

        return tokens

    def searchTokenLookUp(self, node):
        for tempNode in self._token_lookup:
            if tempNode.token == node.token:
                return True, tempNode
        return False, None

    def _insert_node(self, node: Node) -> Node:
        """Takes a node and inserts it into the graph, if a node with the same token exists it returns the existing node
        and merges the information from the new node. This ensures that all pointers to that node remain intact.

        :param Node node: the node to insert
        :return Node: the node that was inserted or merged
        """
        ifInTokenLookUp, nodeInTokenLookUp = self.searchTokenLookUp(node)
        if ifInTokenLookUp:
            node = nodeInTokenLookUp.merge(node)
        # if node in self._token_lookup.values():
        #     # found node so merge and get the new node
        #     node = self._token_lookup[node].merge(node)
        else:
            # empty graph or didn't find the node
            self.roots.append(node)

        return node

    def _update_lookup(self, node: Node):
        """This updates the lookup dictionary, this is all internal and is used to ensure we don't duplicate nodes, this
        is only for object nodes, it ignores relation nodes because we want those to duplicate, they are too common.

        :param Node node:
        """
        self._visited = []
        self._update_lookup_helper(node)

    def _update_lookup_helper(self, node: Node):
        """This updates the token lookup, that is used to locate a token within the graph, it recurses until it finds
        one that is in it, because that means that we have hit an existing node

        :param Node node: the node to update
        """
        if node in self._visited:
            return

        self._visited.append(node)
        ifInTokenLookUp, nodeInTokenLookUp = self.searchTokenLookUp(node)
        # if node.speech_type != RELATION and node not in self._token_lookup:
        #     self._token_lookup[node.token] = node
        if node.speech_type != RELATION and not ifInTokenLookUp:
            self._token_lookup.append(node)
        # update for all of the children
        for child in node.children:
            self._update_lookup_helper(child)

    def _insert_triple_nodes(self, subject_tokens: List[Dict],
                             relation_tokens: List[Dict],
                             object_tokens: List[Dict], sentence) -> Node:
        """This takes the tokens from the triple and creates the appropriate nodes, it checks if the object node already
        exists (not the subject node) and merges the node to link it up. The subject node has everything linked to it.

        :param List[str] subject_tokens: tokens for subject
        :param List[str] relation_tokens: tokens for relation
        :param List[str] object_tokens: tokens for object
        :param Sentence sentence: the sentence that the tokens are in
        :return Node: root subject node
        """
        # add the subject tokens, it connects them like (little -> lamb) would be two subject nodes with lamb as
        # child to parent
        # if subject_tokens:
        #     popped_token = subject_tokens.pop(0)
        # elif object_tokens:
        #     popped_token = object_tokens.pop(0)
        popped_token = subject_tokens.pop(0)

        subject_node = Node(popped_token["stemmed_word"], OBJECT, sentence, first_actual_word=
                            popped_token["actual_word"])

        subject_node = self._insert_node(subject_node)
        self._update_lookup(subject_node)

        current_subject = subject_node

        if subject_tokens:
            current_subject = self._insert_triple_children(current_subject, subject_tokens, OBJECT, sentence)
        # add relation tokens
        current_relation = self._insert_triple_children(
            current_subject, relation_tokens, RELATION, sentence, False)
        if object_tokens:
            # add the object tokens
            self._insert_triple_children(current_relation, object_tokens, OBJECT, sentence)

        return subject_node

    def _insert_triple_children(self,
                                current_node: Node,
                                tokens: List[Dict],
                                part_of_speech: str,
                                sentence,
                                is_object: bool = True):
        """This recursively inserts the list of tokens (which are in the order the occured in, e.g. 'Little lamb' would
        be ['little', 'lamb'] and assembles a subgraph which it attaches to the parent.

        :param Node current_node: whatever the parent node should be
        :param List[str] tokens: the tokenized version of the triple element
        :param str part_of_speech: which pos the tokens belong to
        :param Sentence sentence: the sentence the tokens are part of
        :param bool is_object: switch to treat object and relation differently, e.g. don't add to lookup dict
        :return:
        """
        for token in tokens:
            # construct the token
            to_add = Node(token["stemmed_word"], part_of_speech, sentence,
                          first_actual_word=token["actual_word"])
            ifInTokenLookUp, nodeInTokenLookUp = self.searchTokenLookUp(to_add)

            # see if this object already exists
            # if ifInTokenLookUp and is_object:
            if ifInTokenLookUp:
                to_add = nodeInTokenLookUp.merge(to_add)
            else:
                # self._token_lookup[to_add] = to_add
                self._token_lookup.append(to_add)

            # add the child and update the current subject to the child
            current_node = current_node.add_child(to_add)

            if is_object:
                # test if it is a root
                if to_add in self.roots and len(self.roots) > 1:
                    self.roots.remove(to_add)
                    if not self._is_reachable(to_add):
                        self.roots.append(to_add)

        return current_node

    def _is_reachable(self, node):
        """ This is an internal function that makes sure that if we are removing a root that it is still reachable
        in the graph and we aren't amputating a subgraph (e.g. a->b, b->c, c->a and a doesn't get removed)

        :param Node node: the node to test if it is reachable in the current state of the graph
        :return bool: is it in the graph or not
        """
        visited = []

        def _is_reachable_helper(current, node):
            """ helper function that handles the recursion

            :param Node current: where you are in the graph traversal
            :param Node node: the node to find
            :return bool: is it reachable or not
            """
            visited.append(current)
            if current is node:
                return True
            else:
                for child in current.children:
                    if not child in visited:
                        # only return if you found it
                        if (_is_reachable_helper(child, node)):
                            return True
            return False

        # check all roots
        for root in self.roots:
            return _is_reachable_helper(root, node)
        # for root in self.roots:
        #     if _is_reachable_helper(root, node):
        #         return True
        # return False

    def _color_graph(self):
        """ This goes through and assigns a color to each root, then if it encounters an already colored root, then it
        stores them as equivalent."""
        # TODO should ordering be based on subgraph size? Should there be some pruning going on for small graphs?
        current_color = 0

        for root in self.roots:
            current_color = current_color + 1

            nodes_to_visit = [root]
            visited = [root]

            # it barfs if we recurse
            while nodes_to_visit:
                current_node = nodes_to_visit.pop()
                if current_node.color == 0:
                    current_node.color = current_color
                else:
                    if [current_color,
                        current_node.color] not in self._equivalent_colors:
                        self._equivalent_colors.append(
                            [current_color, current_node.color])
                for child in current_node.children:
                    if child not in visited:
                        nodes_to_visit.append(child)
                        visited.append(child)

    def _get_equivalent_colors(self, color: int) -> List[int]:
        """Helper function to get a list of related colors to whatever color we are looking for, color is represented
        by an int, starting at 1 (0 means no color)

        :param int color:
        :return List[int]: the related colors
        """
        pairs = list(
            filter(lambda entry: color in entry, self._equivalent_colors))
        flattened_colors = [item for sublist in pairs for item in sublist]
        if flattened_colors:
            color_index = flattened_colors.index(color)
            flattened_colors.pop(color_index)

        return flattened_colors

    def reorder_roots(self):
        """This clusters the related roots (ones that share ancestors) so that the ordering of the sentences
        will make a bit more sense."""
        self._color_graph()
        tmp_roots = []
        tmp_roots.extend(self.roots)

        self.roots = []

        while tmp_roots:
            root = tmp_roots.pop()
            self.roots.append(root)
            # grab the related colors
            colors = self._get_equivalent_colors(root.color)
            # grab the roots that map to colors and append in order
            related_roots = list(
                filter(lambda root: root.color in colors, tmp_roots))
            for related_root in related_roots:
                self.roots.append(related_root)
                tmp_roots.pop(tmp_roots.index(related_root))

    def sentence_ordering_output(self):
        """ This function returns all sentences in the a sorted order defined by the triple graph
        Goes through every node in the graph
        :return: array of ordered sentenced
        """
        visited = []
        sentence_count = {}

        def node_out(node: Node, counter2) -> str:
            # counter - sentence position
            output = []  # array of ordered sentences
            for sentence in node.sentences:
                if sentence not in sentence_count:  # checks for already added sentence
                    sentence_count[sentence] = True
                    # output += str(sentence) + '\n'
                    # logger.warn("Text: " + sentence.text)
                    # logger.warn("Previous position: " + str(sentence.position))
                    sentence.position = counter2
                    # logger.warn("New position: " + str(sentence.position))
                    output.append(sentence)  # make more sophisticated later
                    counter2 = counter2 + 1
            return output

        sentence_out = []  # all sentences

        def out_helper(node: Node, counter3) -> str:
            output = []
            # if node.speech_type != RELATION and node in visited:
            if node in visited:
                return output

            # if node.speech_type != RELATION:  # ask about relation
            results3 = node_out(node, counter3)
            visited.append(node)
            if len(results3) > 0:
                # logger.warn(str(results3).format(
                #     datetime.datetime.now()))
                # counter3 = results3[len(results3)-1].position + 1
                for y in range(len(results3)):
                    sentence_out.append(results3[y])
                    # output.append(results3[y])

            for child in node.children:
                # output += out_helper(child)
                if len(sentence_out) > 0:
                    counter5 = sentence_out[len(sentence_out) - 1].position + 1
                else:
                    counter5 = 0
                out_helper(child, counter5)
                # if len(results4) > 0:
                #     counter3 = results4[len(results4)-1].position + 1
                # for m in range(len(results4)):
                #     output.append(results4[m])

            # return output

        i = 0
        for root in self.roots:
            # sentence_out += out_helper(root)
            # sentence_out += '\n\n'
            i += 1
            logger.warn('{}: Root ' + str(i).format(
                datetime.datetime.now()))
            if len(sentence_out) == 0:
                counter = 0
            else:
                counter = sentence_out[len(sentence_out) - 1].position + 1

            out_helper(root, counter)
            # results = out_helper(root, counter)
            # for x in range(len(results)):
            #     sentence_out.append(results[x])
        # logger.warn(sentence_out)
        return sentence_out

    def sort_sentences(self) -> None:
        """This sorts the sentences for the document according to the order they are encountered in the triple graph,
        the sorting is saved by updating the position counter in each of the sentences

        :return: None
        """
        visited_nodes = []
        updated_sentences = []
        position_counter = 0

        def sort_sentences_helper(node: Node, position_counter: int) -> int:
            if node not in visited_nodes:
                visited_nodes.append(node)
                for sentence in node.sentences:
                    if not sentence.id in updated_sentences:
                        updated_sentences.append(sentence.id)
                        sentence.position = position_counter
                        sentence.save()
                        position_counter = position_counter + 1

                for child in node.children:
                    position_counter = sort_sentences_helper(child, position_counter)

            return position_counter

        for root in self.roots:
            position_counter = sort_sentences_helper(root, position_counter)

    def __str__(self) -> str:
        """Prints the graph in string format

        :return str:
        """
        visited = []

        def str_helper(node: Node, level: int) -> str:
            """Recursive function to print the node and determine level prefix

            :param Node node: node to print
            :param int level: level of the graph
            :return str:
            """
            prefix = ''
            for i in range(0, level):
                prefix = f'{prefix}-'
            string = f'\n{prefix}{node}'

            if node.speech_type != RELATION and node in visited:
                return f'{string} -- VISITED'

            # this is here and not at the top because of adding the VISITED part of the string and kickout
            visited.append(node)

            for child in node.children:
                string += str_helper(child, level + 1)

            return string

        string = ''
        for root in self.roots:
            string += str(root)
            visited.append(root)
            for child in root.children:
                string += str_helper(child, 1)
            string += '\n\n'

        return string

    def plot_graph(self):
        """Draws a networkx graph, it really only looks decent for smallish graphs"""
        import networkx
        import matplotlib.pyplot as plt
        from networkx.drawing.nx_agraph import graphviz_layout

        i = 0
        graph = networkx.DiGraph()
        for root in self.roots:
            root = _NetworkXNode(root)

            graph.add_node(root)
            nodes_to_visit = [root]
            visited = [root]

            # it barfs if we recurse
            while nodes_to_visit:
                current_node = nodes_to_visit.pop()
                for child in current_node.children:
                    child = _NetworkXNode(child)
                    if child not in visited:
                        graph.add_node(child)
                        graph.add_edge(
                            current_node,
                            child,
                            key=id(child),
                            weight=current_node.children[child.node])
                        nodes_to_visit.append(child)
                        visited.append(child)

            color_map = []
            for node in graph:
                if node.speech_type == RELATION:
                    color_map.append('white')
                else:
                    color_map.append('red')

            # each sub-graph needs to be saved
            # pos = networkx.spring_layout(graph)  # , k=0.3, iterations=20)
            pos = graphviz_layout(graph)
            networkx.draw(
                graph,
                pos,
                node_color=color_map,
                with_labels=True,
                font_size=8)
            # edge_labels = networkx.get_edge_attributes(graph, 'weight')
            # networkx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels)
            # change this if you are not on *nix type of filesystem
            # plt.savefig(f'/tmp/graph-{i}.png')
            plt.savefig('/tmp/graph-{}.png'.format(i))
            graph.clear()
            plt.clf()
            i = i + 1
