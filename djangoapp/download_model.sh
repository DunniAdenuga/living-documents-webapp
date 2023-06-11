# download 1st pre-trained models for pre_summ_summarizer
gdown https://drive.google.com/uc?id=1-IKVCtc4Q-BdZpjXc4s70_fRsWnjtYLr
unzip bertsumextabs_cnndm_final_model.zip
mv model_step_148000.pt bertsumextabs_cnndm_final_model.pt
mv bertsumextabs_cnndm_final_model.pt text_generation/summarizers/pre_summ/pre-trained_models/
rm bertsumextabs_cnndm_final_model.zip

# download 2nd pre-trained models for pre_summ_summarizer
gdown https://drive.google.com/uc?id=1kKWoV0QCbeIuFt85beQgJ4v0lujaXobJ
unzip bertext_cnndm_transformer.zip
mv bertext_cnndm_transformer.pt text_generation/summarizers/pre_summ/pre-trained_models/
rm bertext_cnndm_transformer.zip
