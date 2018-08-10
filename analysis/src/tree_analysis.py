import os
import numpy as np
from os import path
from glob import glob
from itertools import product
from sklearn.externals import joblib
from sklearn.tree import export_graphviz
from pandas import read_csv, DataFrame, concat


class TreeAnalysis:

    @staticmethod
    def grow_trees(model, type_path, max_depth=10, min_samples_split=0.1):
        """Create DecisionTrees for each data set.

        :param model: DecisionTreeRegressor or DecisionTreeClassifier
            Model used to create trees.

        :param type_path: Path object
            Path class used to save data.

        :param max_depth: int (default 10)
            Maximum depth of the tree.

        :param min_samples_split: int, float (default 0.1)
            Minimum samples required to split.
            If int, the number of exact samples.
            If float, the percentage of samples to be used for split.

        :return: None
        """
        model.max_depth = max_depth
        model.min_samples_split = min_samples_split

        dataset_paths = glob(path.join(type_path.data_path, '*'))

        for dataset_path in dataset_paths:
            data = read_csv(dataset_path)
            features = data.columns.values[:-1]
            data = data.values

            x = data[:, :-1]
            y = data[:, -1]
            classes = sorted(set(y)) if type(y[0]) is str else None

            model.fit(x, y)

            dataset_name = dataset_path.split('/')[-1]
            tree_name = dataset_name[:-4]

            # Save as text file
            tree_path = path.join(type_path.text_trees_path, tree_name + '.dot')
            export_graphviz(model,
                            tree_path,
                            feature_names=features,
                            class_names=classes,
                            filled=True)

            # Save as png
            png_tree_path = path.join(type_path.visible_trees_path,
                                      tree_name + '.png')

            os.system('dot -Tpng ' + tree_path + ' -o ' + png_tree_path)

            # Save as object
            obj_tree_path = path.join(type_path.object_trees_path,
                                      tree_name + '.pkl')

            joblib.dump(model.tree_, obj_tree_path)

    @classmethod
    def get_important_nodes(cls, analysis_datapath, type_path):
        """Get the most important nodes.

        :param analysis_datapath: string
            Dataset folder.

        :param type_path: Path object
            Path class used to save data.

        :return: None
        """
        paths = glob(path.join(type_path.data_path, '*'))
        data = read_csv(paths[0], header=0)
        features_names = data.columns.values

        y = data.iloc[:, -1].values
        classes = sorted(set(y)) if type(y[0]) is str else [features_names[-1]]

        trees_filepath = glob(path.join(type_path.object_trees_path, '*'))

        method_types = {'borda': 'scf',
                        'copeland': 'scf',
                        'dowdall': 'scf',
                        'simpson': 'scf',
                        'dtree': 'classif',
                        'gnb': 'classif',
                        'knn': 'classif',
                        'mlp': 'classif',
                        'svc': 'classif',
                        'mean': 'math',
                        'median': 'math',
                        'plurality': 'vote'}

        important_nodes = {}
        columns = ['node_index',
                   'feature',
                   'importance',
                   'impurity',
                   'threshold',
                   'value',
                   'child_left_diff',
                   'child_right_diff',
                   'children_diff']

        for tree_filepath in trees_filepath:
            tree = joblib.load(tree_filepath)

            tree_name = tree_filepath.split('/')[-1][:-4]
            metadata = tree_name.split('_')

            if metadata[0] in method_types.keys():
                tree_name = method_types[metadata[0]] + '_' + tree_name

            importances = tree.compute_feature_importances()
            features = np.argsort(importances)[::-1]

            for feature_i in features:

                if importances[feature_i] == 0:
                    break

                if 3 in data.shape:
                    break

                possible_nodes = np.where(tree.feature == feature_i)[0]

                node_index = possible_nodes[0]  # first node with this feature
                left_i = tree.children_left[node_index]    # his left child
                right_i = tree.children_right[node_index]  # his right child

                feature = features_names[feature_i]
                importance = importances[feature_i]

                values = tree.value[node_index]
                m, n = values.shape

                for i, j in product(range(m), range(n)):
                    value = values[i, j]
                    impurity = tree.impurity[node_index]
                    threshold = tree.threshold[node_index]

                    left_value = tree.value[left_i][0, 0]
                    right_value = tree.value[right_i][0, 0]

                    child_left_diff = left_value - value
                    child_right_diff = right_value - value
                    children_diff = left_value - right_value

                    class_name = classes[j]

                    if class_name in method_types.keys():
                        class_name = method_types[class_name] + '_' + class_name

                    important_nodes.setdefault(class_name, {})
                    important_nodes[class_name].\
                        setdefault(tree_name, DataFrame(columns=columns))

                    ins = DataFrame([node_index,
                                     feature,
                                     importance,
                                     impurity,
                                     threshold,
                                     value,
                                     child_left_diff,
                                     child_right_diff,
                                     children_diff], index=columns).T

                    important_nodes[class_name][tree_name] = \
                        important_nodes[class_name][tree_name].\
                        append(ins, ignore_index=True)

        for class_name in important_nodes:
            important_nodes[class_name] = concat(important_nodes[class_name])

        concat(important_nodes).to_csv(path.join(type_path.trees_path,
                                                 'important_nodes.csv'))

        cls.get_common_nodes(type_path)

    @staticmethod
    def get_common_nodes(type_path):
        data = read_csv(path.join(type_path.trees_path, 'important_nodes.csv'),
                        header=0,
                        index_col=[0, 1])

        methods1, methods2 = zip(*data.index.values)
        methods1, methods2 = list(set(methods1)), list(set(methods2))
        methods = methods1 if len(methods1) > len(methods2) else methods2

        importances_sum = {}

        for method in methods:
            metadata = method.split('_')
            method_type = metadata[0]

            if method_type == 'arb':
                method_type += metadata[1]

            importances_sum.setdefault(method_type, DataFrame())

            if method in methods1:
                rankings = data.loc[method, :]
            else:
                rankings = data.loc[methods1[0], :].loc[method, :]

            m, n = rankings.shape

            for i in range(m):
                ins = rankings.iloc[i, :]
                feature = ins.loc['feature']
                importance = ins.loc['importance']

                try:
                    importances_sum[method_type].loc[feature, 'sum'] += importance
                except KeyError:
                    importance_ins = DataFrame([importance],
                                               index=[feature],
                                               columns=['sum'])

                    importances_sum[method_type] = \
                        importances_sum[method_type].append(importance_ins)

            importances_sum[method_type].sort_values('sum',
                                                     ascending=False,
                                                     inplace=True)

        sums = concat(importances_sum)
        most_important = {}

        method_types, _ = zip(*sums.index.values)
        method_types = set(method_types)

        # Get only the first for each method type
        for method_type in method_types:
            data = sums.loc[method_type, :].iloc[0, :]
            most_important[method_type] = DataFrame(data).T

        concat(most_important).to_csv(path.join(type_path.trees_path,
                                                'most_important_nodes.csv'))