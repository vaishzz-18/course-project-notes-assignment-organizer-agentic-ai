import { useQuery } from '@tanstack/react-query'
import { ScrollText, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'
import { getAuditLog } from '../services/api'

const agentColor: Record<string, string> = {
  AURACoordinator: 'bg-navy-100 text-navy-800',
  NotesRepositoryAgent: 'bg-blue-100 text-blue-800',
  AssignmentDistributionAgent: 'bg-purple-100 text-purple-800',
  SubmissionCollectionAgent: 'bg-indigo-100 text-indigo-800',
  PlagiarismSimilarityAgent: 'bg-orange-100 text-orange-800',
  GradingAssistanceAgent: 'bg-green-100 text-green-800',
  ProjectMilestoneAgent: 'bg-teal-100 text-teal-800',
  GradePublishingAgent: 'bg-emerald-100 text-emerald-800',
  GovernanceEngine: 'bg-gray-100 text-gray-800',
}

function StatusIcon({ status }: { status: string }) {
  if (status === 'success') return <CheckCircle className="w-4 h-4 text-green-500" />
  if (status === 'error') return <XCircle className="w-4 h-4 text-red-500" />
  return <AlertTriangle className="w-4 h-4 text-amber-500" />
}

export default function AuditPage() {
  const { data: logs, isLoading } = useQuery({
    queryKey: ['audit'],
    queryFn: () => getAuditLog().then(r => r.data),
    refetchInterval: 15_000,
  })

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2 mb-6">
        <ScrollText className="w-6 h-6" />
        Audit Log
        <span className="text-sm font-normal text-gray-400 ml-2">— every action, every agent, full traceability</span>
      </h1>

      {isLoading && <p className="text-gray-400">Loading…</p>}

      <div className="space-y-1">
        {logs?.map((log: any) => (
          <div key={log.id} className="flex items-center gap-4 p-3 bg-white rounded-lg border border-gray-100 hover:border-gray-200 transition-colors text-sm">
            <StatusIcon status={log.status} />
            <div className="w-36 flex-shrink-0">
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${agentColor[log.agent_name] || 'bg-gray-100 text-gray-700'}`}>
                {log.agent_name.replace('Agent', '')}
              </span>
            </div>
            <div className="flex-1 font-medium text-gray-800">{log.action}</div>
            {log.entity_type && (
              <div className="text-xs text-gray-400">
                {log.entity_type} #{log.entity_id}
              </div>
            )}
            <div className="text-xs text-gray-400 font-mono w-40 flex-shrink-0 text-right">
              {new Date(log.created_at).toLocaleString()}
            </div>
            <div className="text-xs text-gray-300 font-mono w-20 flex-shrink-0 overflow-hidden text-ellipsis" title={log.run_id}>
              {log.run_id?.slice(0, 8)}…
            </div>
          </div>
        ))}
        {logs?.length === 0 && <p className="text-gray-400">No audit entries yet.</p>}
      </div>
    </div>
  )
}
