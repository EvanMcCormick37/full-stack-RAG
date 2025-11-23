const AnswerInput = ({}) => {
    return (
        <div className='answer-input'></div>
    );
};

const GeneratedQuestion = ({}) => {
    return (
        <div className='generated-question'></div>
    );
};

const QuestionOfInterest = ({}) => {
    return (
        <div className='question-of-interest'>
            <GeneratedQuestion/>
            <AnswerInput/>
        </div>
    );
};