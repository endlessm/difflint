/*
 * Format errors for consumption by a lint-diff tool that compares JSHint output
 * between two revisions of the same file. This reporter is not intended for
 * human consumption.
 */

var resultToFullMessage = function (result) {
    return result.file + "|" + result.error.code + "|" + result.error.reason;
};

var compareResults = function (resultA, resultB) {
    var messageA = resultToFullMessage(resultA);
    var messageB = resultToFullMessage(resultB);
    return messageA.localeCompare(messageB);
};

module.exports = {
    reporter: function (results) {
        var resultsList = results.splice(); // Shallow copy
        resultsList.sort(compareResults);
        resultsList.forEach(function (result) {
            console.log(resultToFullMessage(result));
        });
    }
};
