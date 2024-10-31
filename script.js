// Example data
const stats = {
    totalWords: 100,
    learnedWords: 70,
    unknownWords: 20,
    reviewWords: 10,
};

// Calculate percentages
const learnedPercentage = (stats.learnedWords / stats.totalWords) * 100;
const unknownPercentage = (stats.unknownWords / stats.totalWords) * 100;
const reviewPercentage = (stats.reviewWords / stats.totalWords) * 100;

// Update the HTML with calculated values
document.getElementById('learned-percentage').innerText = `${learnedPercentage.toFixed(2)}%`;
document.getElementById('unknown-percentage').innerText = `${unknownPercentage.toFixed(2)}%`;
document.getElementById('review-percentage').innerText = `${reviewPercentage.toFixed(2)}%`;

// Optional: Change encouragement message based on learning progress
const encouragementMessage = 
    learnedPercentage >= 75 
    ? "You're doing fantastic! Keep it up!" 
    : "Keep up the great work! Every word you learn brings you closer to fluency!";
document.getElementById('encouragement-message').innerText = encouragementMessage;
