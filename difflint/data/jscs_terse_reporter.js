/*
 * Format errors for consumption by a lint-diff tool that compares JSCS output
 * between two revisions of the same file. This reporter is not intended for
 * human consumption.
 */

var errorToFullMessage = function (fname, error) {
    return fname + "|" + error.rule + "|" + error.message;
};

var compareFullMessages = function (filename, errorA, errorB) {
    var messageA = errorToFullMessage(filename, errorA);
    var messageB = errorToFullMessage(filename, errorB);
    return messageA.localeCompare(messageB);
};

module.exports = function (errorsCollection) {
    errorsCollection.forEach(function (errors) {
        var filename = errors.getFilename();
        var errorsList = errors.getErrorList().slice(); // Shallow copy
        errorsList.sort(compareFullMessages.bind(null, filename));
        errorsList.forEach(function (error) {
            console.log(errorToFullMessage(filename, error));
        });
    });
};
