export type DecisionStatus = 'CONFIRMED' | 'PROPOSED' | 'REJECTED' | 'UNRESOLVED'
export type Priority = 'HIGH' | 'MEDIUM' | 'LOW'

export interface Citation {
  segment_id: string
  quote: string
  speaker: string
}

export interface Decision {
  id: string
  description: string
  status: DecisionStatus
  confidence: number
  citation: Citation
}

export interface ActionItem {
  id: string
  title: string
  description: string
  owner: string | null
  deadline: string | null
  priority: Priority
  status: 'OPEN' | 'IN_PROGRESS' | 'DONE'
  citation: Citation
}

export interface MeetingAnalysis {
  id: string
  title: string
  project: string
  analyzed_at: string
  summary: string
  topics: string[]
  decisions: Decision[]
  action_items: ActionItem[]
  open_questions: string[]
  risks: string[]
  transcript: string
  analysis_source?: 'ollama' | 'fallback'
  model?: string | null
  scheduled_at?: string
  attendees?: string[]
}
