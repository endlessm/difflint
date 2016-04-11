/*
 * Format errors for consumption by a lint-diff tool that compares JSCS output
 * between two revisions of the same file. This reporter is not intended for
 * human consumption.
 */

var errorToFullMessage = function (error) {
    return "|" + error.rule + "|" + error.message;
};

var compareFullMessages = function (errorA, errorB) {
    var messageA = errorToFullMessage(errorA);
    var messageB = errorToFullMessage(errorB);
    return messageA.localeCompare(messageB);
};

module.exports = function (errorsCollection) {
    errorsCollection.forEach(function (errors) {
        var filename = errors.getFilename();
        var errorsList = errors.getErrorList().slice(); // Shallow copy
        errorsList.sort(compareFullMessages);
        errorsList.forEach(function (error) {
            console.log(errorToFullMessage(error));
        });
    });
};
