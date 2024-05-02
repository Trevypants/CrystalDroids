let backendUrl;
let userId;

function startChat() {
  userId = document.getElementById('user-id').value;
  // Hide the User ID section
  document.getElementById('chat-container').innerHTML = `
      <h2>Chat</h2> 
      <div id="chat-box"></div> 
      <input type="text" id="message-input">
      <button onclick="sendMessage()">Send</button>
    `;
}

async function sendMessage() {
  const message = document.getElementById('message-input').value;
  document.getElementById('message-input').value = '';

  // Display user message
  displayMessage('You', message);

  // Send POST request to your Gen AI API endpoint 
  console.log(`Sending POST request to ${backendUrl}/chat/${userId}`)
  const response = await fetch(`${backendUrl}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: message })
  })
  const data = await response.json();
  console.log(`Received response: ${data}`);

  // Display AI response
  displayMessage('Doctor Fresh', data.text);
}

function displayMessage(sender, message) {
  const chatBox = document.getElementById('chat-box');
  chatBox.innerHTML += `
      <p><strong>${sender}:</strong> ${message}</p> 
    `;
}