Comments = window.Comments || {};

    

(function(exports, $) {
    /* Template string for rendering success or error messages. */
    var alertMarkup = (
        '<div class="alert alert-{class} alert-dismissable">' +
        '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button>' +
        '<strong>{title}</strong> {body}</div>');
    
    function displayNoComments() {
        noComments = $('<h3>', {
            'text': 'No comments have been posted yet.'});
        $('h4#comment-form').before(noComments);
    }
    
    /* Template string for rendering a comment. */
    var commentTemplate = (
        '<div class="media">' +
        '<a class="pull-left" href="{url}">' +
        '<img class="media-object" src="{gravatar}" />' +
        '</a>' +
        '<div class="media-body">' +
        '<h4 class="media-heading">{created_timestamp}</h4>{body}' +
        '</div></div>'
    );

    var imageTemplate = (
        '<div class="media">' +
        '<a class="pull-left" href="{contentUrl}">' +
        '<img class="media-object" src="{thumbnailUrl}" />' +
        '</a>' +
        '<div class="media-body">' +
        '<h4 class="media-heading">{name}</h4>{encodingFormat}' +
        '</div></div>'
    );

    function renderComment(comment) {
        var createdDate = new Date(comment.created_timestamp).toDateString();
        return (commentTemplate
            .replace('{url}', comment.url)
            .replace('{gravatar}', comment.gravatar)
            .replace('{created_timestamp}', createdDate)
            .replace('{body}', comment.body));
    }

    function renderImage(image) {
        var createdDate = new Date(image.created_timestamp).toDateString();
        return (imageTemplate
            .replace('{name}', image.name)
            .replace('{thumbnailUrl}', image.thumbnailUrl)
            .replace('{contentUrl}', image.contentUrl)
            .replace('{encodingFormat}', image.encodingFormat));
    }

    function displayComments(comments) {
        $.each(comments, function(idx, comment) {
            var commentMarkup = renderComment(comment);
            $('h4#comment-form').before($(commentMarkup));
        });
    }

    function displayImages(images) {
        $.each(images, function(idx, image) {
            var imageMarkup = renderImage(image);
            $('h4#comment-form').before($(imageMarkup));
        });
    }

    function load(entryId) {
        var filters = [{
            'name': 'entry_id',
            'op': 'eq',
            'val': entryId}];
        var serializedQuery = JSON.stringify({'filters': filters});
        $.get('/api/comment', {'q': serializedQuery}, function(data) {
            if (data['num_results'] === 0) {
                displayNoComments();
            } else {
                displayComments(data['objects']);
            }
        });
    }

    function loadimage(keyword) {
        var filters = [{
            'val': keyword }];
        var params = {
            // Request parameters
            "q": keyword,
            "count": "10",
            "offset": "0",
            "mkt": "en-us",
            "safeSearch": "Moderate",
        };

        $.ajax({
            url: "https://api.cognitive.microsoft.com/bing/v7.0/images/search?" + $.param(params),
            beforeSend: function(xhrObj){
                // Request headers
                xhrObj.setRequestHeader("Ocp-Apim-Subscription-Key","d94125558b884a309dd71f9e1aa8b9fb");
            },
            type: "GET",
            // Request body
            data: "{body}",
        })
        .done(function(data) {
            if (data) {
                displayImages(data['value']);
                alert("success");
            } else {
                displayNoComments();
                alert("error");
            }
        })
        .fail(function() {
            //displayNoComments();
            alert("error");
        });

        // $.get('https://api.cognitive.microsoft.com/bing/v7.0/images/search?', {'q': keyword}, function(data) {
        //     if (data['num_results'] === 0) {
        //         displayNoComments();
        //     } else {
        //         displayComments(data['objects']);
        //     }
        // });
    }

    /* Create an alert element. */
    function makeAlert(alertClass, title, body) {
        var alertCopy = (alertMarkup
            .replace('{class}', alertClass)
            .replace('{title}', title)
            .replace('{body}', body));
        return $(alertCopy);
    }
    /* Retrieve the values from the form fields and return as an object. */
    function getFormData(form) {
        return {
            'name': form.find('input#name').val(),
            'email': form.find('input#email').val(),
            'url': form.find('input#url').val(),
            'body': form.find('textarea#body').val(),
            'entry_id': form.find('input[name=entry_id]').val()
        }
    }
    function bindHandler() {
    /* When the comment form is submitted, serialize the form data as JSON and POST it to the API. */
        $('form#comment-form').on('submit', function() {
            var form = $(this);
            var formData = getFormData(form);
            var request = $.ajax({
                url: form.attr('action'),
                contentType: 'application/json; charset=utf-8',
                type: 'POST',
                data: JSON.stringify(formData),
                dataType: 'json'
            });
            request.success(function(data) {
                alertDiv = makeAlert('success', 'Success', 'your comment was posted.');
                form.before(alertDiv);
                form[0].reset();
            });
            request.fail(function() {
                alertDiv = makeAlert('danger', 'Error', 'your comment was not posted.');
                form.before(alertDiv);
            });
            return false;
        });
    }
    exports.load = load;
    exports.loadimage = loadimage;
    exports.bindHandler = bindHandler;

})(Comments, jQuery);