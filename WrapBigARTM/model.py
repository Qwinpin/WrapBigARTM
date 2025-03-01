# Currently only main and back topics and text modality are supported

import artm

# {SmoothSparsePhiRegularizer : [{topic_type: 'main' or 'back'
# topic_names: , tau: , }, {}],
# }

def reset_regularizers(model_artm, regularizers_dict):
    topic_names = model_artm.topic_names

    available_regs_dict = {
        'SmoothSparsePhiRegularizer': artm.SmoothSparsePhiRegularizer,
        'SmoothSparseThetaRegularizer': artm.SmoothSparseThetaRegularizer,
        'DecorrelatorPhiRegularizer': artm.DecorrelatorPhiRegularizer
    }

    for reg in regularizers_dict.keys():
        for i in range(len(regularizers_dict[reg])):
            ttype = available_regs_dict[reg][i]['topic_type']
            model_artm.regularizers.add(
                available_regs_dict[reg](
                    name=''.join([reg, ttype]),
                    topic_names=[name for name in topic_names if name.startswith(ttype)],
                    tau=available_regs_dict[reg][i]['tau']),
                overwrite=True)

    return model_artm


def init_score_tracker(model_artm, my_dictionary, class_id='text'):
    model_artm.scores.add(artm.PerplexityScore(
        name='PerplexityScore', dictionary=my_dictionary),
        overwrite=True)

    model_artm.scores.add(artm.SparsityPhiScore(
        name='SparsityPhiScore', class_id=class_id),
        overwrite=True)

    model_artm.scores.add(artm.SparsityThetaScore(
        name='SparsityThetaScore'),
        overwrite=True)

    model_artm.scores.add(artm.TopTokensScore(
        name="top_words", num_tokens=200, class_id=class_id),
        overwrite=True)

    model_artm.scores.add(artm.TopicKernelScore(
        name='TopicKernelScore', class_id=class_id, probability_mass_threshold=0.6),
        overwrite=True)
    print('Scores are set!')


def dictionary_initialization(model_artm, batches_dir, min_df, max_tf):
    my_dictionary = artm.Dictionary()
    my_dictionary.gather(data_path=batches_dir)
    my_dictionary.filter(min_df=min_df, max_tf=max_tf)
    model_artm.initialize(my_dictionary)

    return model_artm, my_dictionary


def init_model(T, B, batches_dir, regularizers_dict, num_document_passes=30,
               weights_dict=None, min_df=None, max_tf=None):
    T = int(T)
    B = int(B)
    main_topics_num = T
    model_artm = artm.ARTM(
        num_topics=T + B,
        topic_names=["topic{}".format(i) if i < main_topics_num else "back{}".format(i) for i in range(B)],
        cache_theta=True,
        show_progress_bars=True,
        class_ids=weights_dict,
        num_document_passes=num_document_passes)

    topic_names = model_artm.topic_names
    model_artm, my_dictionary = dictionary_initialization(model_artm, batches_dir, min_df, max_tf)
    print("Model is initialized!")

    if regularizers_dict:
        model_artm = reset_regularizers(model_artm, regularizers_dict)
    model_artm = init_score_tracker(model_artm, my_dictionary)
    return model_artm


def train_model(model_artm, batch_vectorizer, num_collection_passes=20):
    model_artm.fit_offline(batch_vectorizer, num_collection_passes=num_collection_passes)
    print('Model is fitted!')

    return model_artm
