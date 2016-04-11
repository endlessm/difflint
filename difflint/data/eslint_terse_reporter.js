/*
 * Format errors for consumption by a lint-diff tool that compares JSHint output
 * between two revisions of the same file. This reporter is not intended for
 * human consumption.
 */

var formatMessage = function (filename, message) {
    // These criteria match the criteria for displaying "error" in the default
    // reporter for eslint.
    if (message.fatal || message.severity === 2) {
        var messageType = "error";
    }
    else {
        var messageType = "warning";
    }
    return filename + "|" + messageType + "|" + message.message;
};

var compareMessages = function (filename, messageA, messageB) {
    var formattedMessageA = formatMessage(filename, messageA);
    var formattedMessageB = formatMessage(filename, messageB);
    return formattedMessageA.localeCompare(formattedMessageB);
};

module.exports = function(results) {
    if (results.length === 0) {
        return "";
    }
    else if (results.length > 1 {
        throw new Error("Lint reporting applied to more " +
                        "than one file at once!");
    }

    // We only apply this function to a single file at a time,
    // so we should only have a single result.
    var result = results[0];
    var filePath = result.filePath;
    var messageList = result.messages.slice(); // Shallow copy.
    messageList.sort(compareMessages.bind(null, filePath));
    messageList.forEach(function (message) {
        console.log(formatMessage(filePath, message));
    });
};
