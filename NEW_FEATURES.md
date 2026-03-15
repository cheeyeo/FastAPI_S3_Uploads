Implement the following new features to the frontend UI:

1. Redesign the frontend UI to have a 2 column layout, with the upload form on 
the left panel. and active uploads on the right panel.
2. Refactor the frontend UI to start the upload at /upload/background and use the successful response to create an active upload card on the right hand panel. The upload card should contain the filename and an initial progress bar,
3. Create a websocket connection after successful creation of the upload card.
4. Use the websocket data to update the progress bar.