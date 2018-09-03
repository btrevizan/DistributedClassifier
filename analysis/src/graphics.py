import ete3
import numpy as np
import matplotlib.pyplot as plt

from os import path
from glob import glob
from pandas import read_csv
from .path import RegressionPath
from sklearn.cluster import AgglomerativeClustering


class Boxplot:

    def __init__(self, metric='f1_macro'):
        self.rankings = []
        self.ordered_methods = []
        self.metric = metric

    def show(self):
        """Show boxplot."""
        plt.show()

    def save(self, filename):
        """Save figure in Path.graphics_path.

        :param filename: String
            File name.

        :return: None
        """
        plt.savefig(path.join(RegressionPath().graphics_path, filename), bbox_inches='tight')

    def ranking(self):
        """Create a boxplot by ranking."""
        self.__get_ranking()
        self.__make('Rank Position')

    def performance(self):
        """Create a boxplot by ranking."""
        self.__get_performance()
        self.__make('F1 Score')

    def __get_ranking(self, datasets_folders=[]):
        type_path = RegressionPath()
        metric = [self.metric, 'f1'] if 'f1_' in self.metric else [self.metric, self.metric]
        classifiers = ['gnb', 'dtree', 'svc', 'knn', 'mlp']
        tests_path = '../evaluation/tests/'

        if len(datasets_folders) == 0:
            datasets_folders = [p for p in glob(path.join(tests_path, '*')) if path.isdir(p)]

        for folder in datasets_folders:
            data = read_csv(path.join(folder, type_path.default_file),
                            header=[0, 1], index_col=0)

            try:
                data = data.loc[:, 'mean'].loc[:, metric[0]]
            except KeyError:
                data = data.loc[:, 'mean'].loc[:, metric[1]]

            data = data.sort_values()
            methods = list(data.index.values)

            i = 0
            while len(methods) < 32:
                methods.append(classifiers[i])
                i += 1

            methods = list(map(lambda x: type_path.concat_method_type(x), methods))
            positions = list(enumerate(methods))

            # Sort by name
            positions.sort(key=lambda x: x[1])
            ranking, ordered_methods = zip(*positions)

            # From 1 to 32
            ranking = list(map(lambda x: x + 1, ranking))
            self.rankings.append(ranking)

        self.ordered_methods = ordered_methods

    def __get_performance(self, datasets_folders=[]):
        type_path = RegressionPath()
        metric = [self.metric, 'f1'] if 'f1_' in self.metric else [self.metric, self.metric]
        classifiers = ['gnb', 'dtree', 'svc', 'knn', 'mlp']
        tests_path = '../evaluation/tests/'

        if len(datasets_folders) == 0:
            datasets_folders = [p for p in glob(path.join(tests_path, '*')) if path.isdir(p)]

        for folder in datasets_folders:
            data = read_csv(path.join(folder, type_path.default_file),
                            header=[0, 1], index_col=0)

            try:
                data = data.loc[:, 'mean'].loc[:, metric[0]]
            except KeyError:
                data = data.loc[:, 'mean'].loc[:, metric[1]]

            data = data.sort_values()
            ranking = list(data.values)
            methods = list(data.index.values)

            i = 0
            while len(methods) < 32:
                methods.append(classifiers[i])
                ranking.append(0)
                i += 1

            methods = list(map(lambda x: type_path.concat_method_type(x), methods))
            positions = zip(methods, ranking)
            positions = sorted(positions, key=lambda x: x[0])
            methods, ranking = zip(*positions)
            self.rankings.append(list(ranking))

        self.ordered_methods = list(methods)

    def __make(self, ylabel):
        m, n = len(self.rankings), len(self.rankings[0])
        boxplot_data = np.reshape(self.rankings, (m, n))

        fig, ax = plt.subplots()
        ax.boxplot(boxplot_data)

        ax.set_xlabel('Methods')
        ax.set_ylabel(ylabel)
        ax.set_xticklabels(self.ordered_methods, rotation=90)
        plt.yticks(range(int(boxplot_data.min()), int(boxplot_data.max()) + 1))


class NewickTree:
    """
    =============================================================================
    Various Agglomerative Clustering on a 2D embedding of digits
    =============================================================================

    An illustration of various linkage option for agglomerative clustering on
    a 2D embedding of the digits dataset.

    The goal of this example is to show intuitively how the metrics behave, and
    not to find good clusters for the digits. This is why the example works on a
    2D embedding.

    What this example shows us is the behavior "rich getting richer" of
    agglomerative clustering that tends to create uneven cluster sizes.
    This behavior is especially pronounced for the average linkage strategy,
    that ends up with a couple of singleton clusters.

    # Authors: Gael Varoquaux
    # License: BSD 3 clause (C) INRIA 2014
    """
    def create(self, linkage='ward'):
        """
        Create a Newick Tree and display it.

        :param linkage: str {(Default 'ward'), 'average', 'complete'}
            Agglomerative method.

        :return: None
        """
        data = read_csv('data/datasets.csv')
        X = data.values[:, :-1]
        y = data.values[:, -1]

        np.random.seed(0)

        clusterer = AgglomerativeClustering(linkage=linkage, n_clusters=X.shape[0])
        clusterer.fit(X)

        spanner = self.__get_cluster_spanner(clusterer)
        newick_tree = self.__build_newick_tree(clusterer.children_, clusterer.n_leaves_, X, y, spanner)
        tree = ete3.Tree(newick_tree)
        tree.show()

    def __build_newick_tree(self, children, n_leaves, X, leaf_labels, spanner):
        """
        build_Newick_tree(children,n_leaves,X,leaf_labels,spanner)

        Get a string representation (Newick tree) from the sklearn
        AgglomerativeClustering.fit output.

        Input:
            children: AgglomerativeClustering.children_
            n_leaves: AgglomerativeClustering.n_leaves_
            X: parameters supplied to AgglomerativeClustering.fit
            leaf_labels: The label of each parameter array in X
            spanner: Callable that computes the dendrite's span

        Output:
            ntree: A str with the Newick tree representation

        """
        return self.__go_down_tree(children, n_leaves, X, leaf_labels, len(children) + n_leaves - 1, spanner)[0] + ';'

    def __go_down_tree(self, children, n_leaves, X, leaf_labels, nodename, spanner):
        """
        go_down_tree(children,n_leaves,X,leaf_labels,nodename,spanner)

        Iterative function that traverses the subtree that descends from
        nodename and returns the Newick representation of the subtree.

        Input:
            children: AgglomerativeClustering.children_
            n_leaves: AgglomerativeClustering.n_leaves_
            X: parameters supplied to AgglomerativeClustering.fit
            leaf_labels: The label of each parameter array in X
            nodename: An int that is the intermediate node name whos
                children are located in children[nodename-n_leaves].
            spanner: Callable that computes the dendrite's span

        Output:
            ntree: A str with the Newick tree representation

        """
        nodeindex = nodename - n_leaves
        if nodename < n_leaves:
            return leaf_labels[nodeindex], np.array([X[nodeindex]])
        else:
            node_children = children[nodeindex]
            branch0, branch0samples = self.__go_down_tree(children, n_leaves, X, leaf_labels, node_children[0], spanner)
            branch1, branch1samples = self.__go_down_tree(children, n_leaves, X, leaf_labels, node_children[1], spanner)
            node = np.vstack((branch0samples, branch1samples))
            branch0span = spanner(branch0samples)
            branch1span = spanner(branch1samples)
            nodespan = spanner(node)
            branch0distance = nodespan - branch0span
            branch1distance = nodespan - branch1span
            nodename = '({branch0}:{branch0distance},{branch1}:{branch1distance})'.format(branch0=branch0,
                                                                                          branch0distance=branch0distance,
                                                                                          branch1=branch1,
                                                                                          branch1distance=branch1distance)
            return nodename, node

    def __get_cluster_spanner(self, aggClusterer):
        """
        spanner = get_cluster_spanner(aggClusterer)

        Input:
            aggClusterer: sklearn.cluster.AgglomerativeClustering instance

        Get a callable that computes a given cluster's span. To compute
        a cluster's span, call spanner(cluster)

        The cluster must be a 2D numpy array, where the axis=0 holds
        separate cluster members and the axis=1 holds the different
        variables.

        """
        if aggClusterer.linkage == 'ward':
            if aggClusterer.affinity == 'euclidean':
                spanner = lambda x: np.sum((x - aggClusterer.pooling_func(x, axis=0)) ** 2)
        elif aggClusterer.linkage == 'complete':
            if aggClusterer.affinity == 'euclidean':
                spanner = lambda x: np.max(np.sum((x[:, None, :] - x[None, :, :]) ** 2, axis=2))
            elif aggClusterer.affinity == 'l1' or aggClusterer.affinity == 'manhattan':
                spanner = lambda x: np.max(np.sum(np.abs(x[:, None, :] - x[None, :, :]), axis=2))
            elif aggClusterer.affinity == 'l2':
                spanner = lambda x: np.max(np.sqrt(np.sum((x[:, None, :] - x[None, :, :]) ** 2, axis=2)))
            elif aggClusterer.affinity == 'cosine':
                spanner = lambda x: np.max(np.sum((x[:, None, :] * x[None, :, :])) / (
                            np.sqrt(np.sum(x[:, None, :] * x[:, None, :], axis=2, keepdims=True)) * np.sqrt(
                        np.sum(x[None, :, :] * x[None, :, :], axis=2, keepdims=True))))
            else:
                raise AttributeError('Unknown affinity attribute value {0}.'.format(aggClusterer.affinity))
        elif aggClusterer.linkage == 'average':
            if aggClusterer.affinity == 'euclidean':
                spanner = lambda x: np.mean(np.sum((x[:, None, :] - x[None, :, :]) ** 2, axis=2))
            elif aggClusterer.affinity == 'l1' or aggClusterer.affinity == 'manhattan':
                spanner = lambda x: np.mean(np.sum(np.abs(x[:, None, :] - x[None, :, :]), axis=2))
            elif aggClusterer.affinity == 'l2':
                spanner = lambda x: np.mean(np.sqrt(np.sum((x[:, None, :] - x[None, :, :]) ** 2, axis=2)))
            elif aggClusterer.affinity == 'cosine':
                spanner = lambda x: np.mean(np.sum((x[:, None, :] * x[None, :, :])) / (
                            np.sqrt(np.sum(x[:, None, :] * x[:, None, :], axis=2, keepdims=True)) * np.sqrt(
                        np.sum(x[None, :, :] * x[None, :, :], axis=2, keepdims=True))))
            else:
                raise AttributeError('Unknown affinity attribute value {0}.'.format(aggClusterer.affinity))
        else:
            raise AttributeError('Unknown linkage attribute value {0}.'.format(aggClusterer.linkage))

        return spanner
