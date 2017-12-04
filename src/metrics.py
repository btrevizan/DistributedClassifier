import numpy as np

from pandas import DataFrame
from sklearn import metrics as met


def cv_score(scores):
    """Build a score matrix where a fold is a line and a scorer a column.

    Keyword arguments:
        scores -- a list of scores from cross_validate's sklearn function
    """
    # Initialize structure
    score_matrix = dict()

    # For each iteration of CV...
    for score in scores:

        # Delete unwanted data
        try:
            del score['fit_time']
            del score['score_time']
        except KeyError:
            pass

        # For each test score...
        for key, values in score.items():

            # Filter scores. Get just the test scores
            if key.startswith('test_'):
                # Delete test_ prefix
                scorer = key.replace('test_', '')

                # Append scores to the scorer
                arr = score_matrix.get(scorer, [])
                score_matrix[scorer] = np.append(arr, values)

    # Convert dict to DataFrame where
    # keys are columns
    return DataFrame.from_dict(score_matrix)


def summary(scores):
    """Average scores from Cross-Validation.

    Keyword arguments:
        scores -- DataFrame or list of DataFrames
    """
    # Make score as list of DataFrames
    scores = scores if type(scores) is list else [scores]

    # Mean matrix
    means = dict()

    # For each CV scores, calculate mean...
    for i in range(len(scores)):
        score = scores[i]
        columns = score.columns

        # ... and append to mean matrix
        mean = score.mean(0)

        means[i] = list(mean.iloc[:])

    df = DataFrame.from_dict(means).T
    df.columns = columns

    return df

###############################################################################
################################## SCORERS ####################################
###############################################################################
def sensitivity_score(y_true, y_pred, **kwargs):
    """Return a sensitivity score (true positive rate)."""
    cm = met.confusion_matrix(y_true, y_pred)

    tp = cm[1,1]
    fn = cm[1,0]

    return tp / (tp + fn)


def specificity_score(y_true, y_pred, **kwargs):
    """Return a specificity score (true negative rate)."""
    cm = met.confusion_matrix(y_true, y_pred)

    tp = cm[1,1]
    fn = cm[1,0]
    fp = cm[0,1]
    tn = cm[0,0]

    return tn / (tn + fp)
