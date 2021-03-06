#!/usr/bin/python3

"""
This file will contain the main script.
"""
import numpy as np
from settings import Settings
import os.path as osp

from helpers import load_embeddings
from helpers import retrieve_SIMLEX999_data_dict, retrieve_MEN_data_dict, compute_correlations
from helpers import retrieve_word_analogy_data_dict, normalised_word_embeddings_data
from helpers import create_bStars_preds_data, compute_accuracy_and_MRR, retrieve_random_examples
from helpers import reduce_dimensions, visualize_embeddings, cluster, save_clusters


def main(opt):

    # Load word embeddings into dictionaries
    deps = load_embeddings(osp.join(opt.emb_path, "deps.words"))
    bow2 = load_embeddings(osp.join(opt.emb_path, "bow2.words"))
    bow5 = load_embeddings(osp.join(opt.emb_path, "bow5.words"))

    # Easy iteration and printing
    emb_names = ['deps', 'bow2', 'bow5']
    embeddings = [deps, bow2, bow5]
    # emb_names = ['deps']
    # embeddings = [deps]

    if (opt.exercise == 3 or opt.exercise == 1):
        # Load similarity dataset into dictionaries
        simlex = retrieve_SIMLEX999_data_dict(osp.join(opt.data_path, "SimLex-999.txt"))
        men = retrieve_MEN_data_dict(osp.join(opt.data_path, 'MEN_dataset_natural_form_full'))

        # Test with cosine, pearson, spearman, simlex, MEN
        p_sim, s_sim, top_sim = compute_correlations(embeddings, simlex, opt.N)
        p_men, s_men, top_men = compute_correlations(embeddings, men, opt.N)

        # Print Quantitative results
        for i, name in enumerate(emb_names):
            print("pearson: {}, spearman: {} for SimLex with {} embeddings".format(p_sim[i], s_sim[i], name))
            print("pearson: {}, spearman: {} for MEN with {} embeddings".format(p_men[i], s_men[i], name))

        # Write qualitative results to file
        for i, name in enumerate(emb_names):
            with open(osp.join(opt.out_path, name+"_similarities.txt"), 'w', encoding='utf8') as f:
                f.write("Top {} most similar pairs on SimLex with {} embeddings.\n".format(opt.N, name))
                for pair in top_sim[i]:
                    f.write("{}: {}\n".format(pair[1], pair[0]))
                f.write("\n")
                f.write("Top {} most similar pairs on MEN with {} embeddings.\n".format(opt.N, name))
                for pair in top_men[i]:
                    f.write("{}: {}\n".format(pair[1], pair[0]))

    elif (opt.exercise == 4 or opt.exercise == 1):
        word_analogy_data = retrieve_word_analogy_data_dict(
            osp.join(opt.data_path, "word-analogy.txt"), opt.split_dataset, opt.lowercase)

        if (opt.extract_N_examples > 0):
            random_examples = retrieve_random_examples(word_analogy_data, opt.extract_N_examples)
            for i, dataset in enumerate(embeddings):
                print("\nCurrently working on embedding: " + emb_names[i] + ".")
                normalised_dataset_data = normalised_word_embeddings_data(dataset)
                bStars_preds_data, _ = create_bStars_preds_data(normalised_dataset_data[0], random_examples, 0)
                inner_products = np.dot(normalised_dataset_data[2], bStars_preds_data[1])
                for j, target_pair in enumerate(bStars_preds_data[0]):
                    indices = np.argsort(-inner_products[:, j])
                    print("Target pair: " + target_pair[0] + " --> " + target_pair[1] + ". Ordered choices: ", end="")
                    for index in indices[:15]:
                        print(normalised_dataset_data[1][index] + ", ", end="")
                    print()

        else:
            for i, dataset in enumerate(embeddings):
                print("\nCurrently working on embedding: " + emb_names[i] + ".")

                acc_f, mrr_f, acc_t, mrr_t, number_of_queries = [0, 0, 0, 0, 0]

                normalised_dataset_data = normalised_word_embeddings_data(dataset)

                for j, subset in enumerate(word_analogy_data):

                    bStars_preds_data, number_of_queries = create_bStars_preds_data(normalised_dataset_data[0],
                                                                                    subset, number_of_queries)

                    inner_products = np.dot(normalised_dataset_data[2], bStars_preds_data[1])

                    acc_f, mrr_f = compute_accuracy_and_MRR(bStars_preds_data[0], normalised_dataset_data[1],
                                                            inner_products, acc_f, mrr_f, False)
                    acc_t, mrr_t = compute_accuracy_and_MRR(bStars_preds_data[0], normalised_dataset_data[1],
                                                            inner_products, acc_t, mrr_t, True)

                print("\nEmbedding: " + emb_names[i] + " ||| " +
                      "Accuracy = " + "{:3.2f}".format(100*acc_t/number_of_queries) + "% (" +
                      "{:3.2f}".format(100*acc_f/number_of_queries) + "%) ||| " +
                      "MRR = " + "{:.2f}".format(mrr_t/number_of_queries) + " (" +
                      "{:.2f}".format(mrr_f/number_of_queries) + ")" +
                      " ||| Total number of queries: " + str(number_of_queries) + "\n\n\n")

    elif (opt.exercise == 5 or opt.exercise == 1):
        # Load nouns
        with open(osp.join(opt.data_path, 'nouns.txt'), 'r', encoding='utf8') as f:
            nouns = f.read().split()

        # Return embedding matrices ordered as the nouns list
        embeddings_nouns = []
        for embedding in embeddings:
            embeddings_nouns.append(np.array([embedding[noun] for noun in nouns]))

        # Reduce dimensions of noun embeddings
        reduced_embeddings = reduce_dimensions(embeddings_nouns,
                                               opt.dim, opt.red_mode, opt.verbose, opt.tsne_dim, opt.tsne_num)

        # Clustering of noun embeddings
        labels = cluster(embeddings_nouns,
                         opt.clu_mode, opt.verbose, opt.k, opt.eps, opt.min_samples)

        # Visualize
        titles = ["{} {} embeddings with {} based cluster labels".format(
            opt.red_mode.capitalize(), name, opt.clu_mode) for name in emb_names]
        visualize_embeddings(reduced_embeddings, labels, titles,
                             opt.viz_num, opt.dim, opt.verbose)

        # Qualitative
        save_clusters(nouns, labels, opt.out_path, ['deps_clusters.txt', 'bow2_clusters.txt', 'bow5_clusters.txt'])


if __name__ == '__main__':
    opt = Settings.args
    main(opt)
