import { AlertTriangle } from 'lucide-react';
import ChatChart from '@/components/chat/ChatChart';
import ChatDataTable from '@/components/chat/ChatDataTable';
import ChatDebugPanel from '@/components/chat/ChatDebugPanel';
import StatusBadge from '@/components/chat/StatusBadge';
import type { ChatMessage as ChatMessageType } from '@/lib/types/aiChat';

interface ChatMessageProps {
  message: ChatMessageType;
  onClarificationClick: (question: string) => void;
}

function renderText(content: string) {
  return content.split('\n').map((line, index) => (
    <span key={`${index}-${line}`}>
      {line}
      <br />
    </span>
  ));
}

export default function ChatMessage({ message, onClarificationClick }: ChatMessageProps) {
  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-lg bg-blue-600 px-4 py-3 text-sm leading-6 text-white">
          {renderText(message.content)}
        </div>
      </div>
    );
  }

  const response = message.response;
  const clarificationQuestions =
    response?.clarificationQuestions?.length
      ? response.clarificationQuestions
      : response?.parsedQuery?.clarification_questions || [];

  return (
    <div className="flex justify-start">
      <div className="w-full max-w-[92%] rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <StatusBadge status={message.status === 'error' ? 'error' : response?.status} />
          {response?.questionType ? <span className="text-xs text-slate-500">{response.questionType}</span> : null}
        </div>

        <div className="text-sm leading-6 text-slate-800">{renderText(message.content)}</div>

        {message.error ? (
          <div className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {message.error}
          </div>
        ) : null}

        {clarificationQuestions.length ? (
          <div className="mt-4 flex flex-wrap gap-2">
            {clarificationQuestions.map((question) => (
              <button
                key={question}
                type="button"
                onClick={() => onClarificationClick(question)}
                className="rounded-md border border-amber-200 bg-amber-50 px-3 py-1.5 text-left text-xs font-medium text-amber-800 hover:bg-amber-100"
              >
                {question}
              </button>
            ))}
          </div>
        ) : null}

        {response?.warnings?.length ? (
          <div className="mt-4 space-y-2">
            {response.warnings.map((warning) => (
              <div
                key={warning}
                className="flex gap-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800"
              >
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                <span>{warning}</span>
              </div>
            ))}
          </div>
        ) : null}

        <ChatChart chart={response?.chart} />
        <ChatDataTable response={response} />
        <ChatDebugPanel response={response} />
      </div>
    </div>
  );
}
