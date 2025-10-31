import { useState, useEffect } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, DollarSign } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Session {
  session_id: string;
  completion_percentage: number;
  current_section: string;
}

interface Document {
  document_id: string;
  filename: string;
  processing_status: string;
  document_type?: string;
  confidence?: number;
}

interface URLAField {
  field_name: string;
  field_type: string;
  required: boolean;
  description: string;
  current_value?: any;
  value_source?: string;
  confidence?: number;
}

interface URLASection {
  section_id: string;
  section_name: string;
  description: string;
  fields: URLAField[];
  completion_percentage: number;
  missing_required_fields: string[];
}

interface IncomeSource {
  source_type: string;
  employer_name?: string;
  amount: number;
  frequency: string;
  is_stable: boolean;
  has_continuance: boolean;
  notes?: string;
}

interface IncomeAnalysis {
  total_monthly_income: number;
  income_sources: IncomeSource[];
  meets_freddie_requirements: boolean;
  issues: string[];
  recommendations: string[];
  potential_income_increases: Array<{
    suggestion: string;
    potential_benefit: string;
  }>;
}

interface InformationGap {
  field_name: string;
  section: string;
  severity: string;
  description: string;
  recommendation: string;
}

interface GapAnalysis {
  total_gaps: number;
  critical_gaps: number;
  warning_gaps: number;
  gaps: InformationGap[];
  completion_percentage: number;
  suggested_documents: string[];
}

interface SystemConfig {
  ai_enabled: boolean;
  provider: string;
  extraction_mode: string;
}

function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [currentSection, setCurrentSection] = useState<URLASection | null>(null);
  const [incomeAnalysis, setIncomeAnalysis] = useState<IncomeAnalysis | null>(null);
  const [gapAnalysis, setGapAnalysis] = useState<GapAnalysis | null>(null);
  const [config, setConfig] = useState<SystemConfig | null>(null);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [activeTab, setActiveTab] = useState('upload');

  useEffect(() => {
    loadConfig();
    createSession();
  }, []);

  const loadConfig = async () => {
    try {
      const response = await fetch(`${API_URL}/config`);
      const data = await response.json();
      setConfig(data);
    } catch (error) {
      console.error('Error loading config:', error);
    }
  };

  const createSession = async () => {
    try {
      const response = await fetch(`${API_URL}/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      const data = await response.json();
      setSession(data);
      loadSection(data.session_id, '1b');
    } catch (error) {
      console.error('Error creating session:', error);
    }
  };

  const loadSession = async () => {
    if (!session) return;
    try {
      const response = await fetch(`${API_URL}/sessions/${session.session_id}`);
      const data = await response.json();
      setSession(data);
    } catch (error) {
      console.error('Error loading session:', error);
    }
  };

  const loadDocuments = async () => {
    if (!session) return;
    try {
      const response = await fetch(`${API_URL}/sessions/${session.session_id}/documents`);
      const data = await response.json();
      setDocuments(data);
    } catch (error) {
      console.error('Error loading documents:', error);
    }
  };

  const loadSection = async (sessionId: string, sectionId: string) => {
    try {
      const response = await fetch(`${API_URL}/sessions/${sessionId}/urla/${sectionId}`);
      const data = await response.json();
      setCurrentSection(data);
    } catch (error) {
      console.error('Error loading section:', error);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || !session) return;

    setUploading(true);
    try {
      for (const file of Array.from(files)) {
        const formData = new FormData();
        formData.append('file', file);

        await fetch(`${API_URL}/sessions/${session.session_id}/documents`, {
          method: 'POST',
          body: formData
        });
      }
      await loadDocuments();
    } catch (error) {
      console.error('Error uploading files:', error);
    } finally {
      setUploading(false);
    }
  };

  const processDocuments = async () => {
    if (!session) return;

    setProcessing(true);
    try {
      await fetch(`${API_URL}/sessions/${session.session_id}/process`, {
        method: 'POST'
      });
      await loadDocuments();
      await loadSection(session.session_id, '1b');
      await loadSession();
      setActiveTab('form');
    } catch (error) {
      console.error('Error processing documents:', error);
    } finally {
      setProcessing(false);
    }
  };

  const calculateIncome = async () => {
    if (!session) return;

    try {
      const response = await fetch(`${API_URL}/sessions/${session.session_id}/income`, {
        method: 'POST'
      });
      const data = await response.json();
      setIncomeAnalysis(data);
      setActiveTab('income');
    } catch (error) {
      console.error('Error calculating income:', error);
    }
  };

  const analyzeGaps = async () => {
    if (!session) return;

    try {
      const response = await fetch(`${API_URL}/sessions/${session.session_id}/gaps`);
      const data = await response.json();
      setGapAnalysis(data);
      setActiveTab('gaps');
    } catch (error) {
      console.error('Error analyzing gaps:', error);
    }
  };

  const updateField = async (fieldName: string, value: any) => {
    if (!session || !currentSection) return;

    try {
      await fetch(`${API_URL}/sessions/${session.session_id}/urla`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          field_name: fieldName,
          value: value,
          section_id: currentSection.section_id
        })
      });
      await loadSection(session.session_id, currentSection.section_id);
    } catch (error) {
      console.error('Error updating field:', error);
    }
  };

  const getConfidenceBadge = (confidence?: number) => {
    if (!confidence) return null;
    const variant = confidence > 0.8 ? 'default' : confidence > 0.5 ? 'secondary' : 'destructive';
    return (
      <Badge variant={variant} className="ml-2">
        {Math.round(confidence * 100)}% confidence
      </Badge>
    );
  };

  const getValueSourceBadge = (source?: string) => {
    if (!source) return null;
    const labels: Record<string, string> = {
      document_ai: 'AI Extracted',
      document_rule: 'Rule Extracted',
      user_input: 'User Input',
      calculated: 'Calculated'
    };
    return (
      <Badge variant="outline" className="ml-2">
        {labels[source] || source}
      </Badge>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Mortgage Application
          </h1>
          <p className="text-gray-600">
            Upload your documents and let us auto-fill your 1003 application
          </p>
        </div>

        {config && !config.ai_enabled && (
          <Alert className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <span className="font-semibold">Running in Rule-based Mode:</span> AI extraction is disabled. 
              Document extraction accuracy may be lower. Please verify all auto-filled values carefully.
            </AlertDescription>
          </Alert>
        )}

        {session && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Application Progress</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Completion</span>
                  <span className="font-semibold">{session.completion_percentage}%</span>
                </div>
                <Progress value={session.completion_percentage} />
              </div>
            </CardContent>
          </Card>
        )}

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="upload">
              <Upload className="w-4 h-4 mr-2" />
              Upload
            </TabsTrigger>
            <TabsTrigger value="form">
              <FileText className="w-4 h-4 mr-2" />
              Form
            </TabsTrigger>
            <TabsTrigger value="income">
              <DollarSign className="w-4 h-4 mr-2" />
              Income
            </TabsTrigger>
            <TabsTrigger value="gaps">
              <AlertCircle className="w-4 h-4 mr-2" />
              Gaps
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Upload Documents</CardTitle>
                <CardDescription>
                  Upload W-2s, paystubs, VOE, bank statements, and other mortgage documents
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                  <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                  <Label htmlFor="file-upload" className="cursor-pointer">
                    <span className="text-blue-600 hover:text-blue-700 font-medium">
                      Click to upload
                    </span>
                    <span className="text-gray-600"> or drag and drop</span>
                  </Label>
                  <Input
                    id="file-upload"
                    type="file"
                    multiple
                    accept=".pdf"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                  <p className="text-sm text-gray-500 mt-2">PDF files only</p>
                </div>

                {documents.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="font-semibold">Uploaded Documents</h3>
                    {documents.map((doc) => (
                      <div
                        key={doc.document_id}
                        className="flex items-center justify-between p-3 bg-white border rounded-lg"
                      >
                        <div className="flex items-center space-x-3">
                          <FileText className="w-5 h-5 text-gray-400" />
                          <div>
                            <p className="font-medium">{doc.filename}</p>
                            <p className="text-sm text-gray-500">
                              Status: {doc.processing_status}
                              {doc.document_type && ` • Type: ${doc.document_type}`}
                            </p>
                          </div>
                        </div>
                        {doc.processing_status === 'completed' && (
                          <CheckCircle className="w-5 h-5 text-green-500" />
                        )}
                      </div>
                    ))}
                  </div>
                )}

                <Button
                  onClick={processDocuments}
                  disabled={documents.length === 0 || processing}
                  className="w-full"
                >
                  {processing ? 'Processing...' : 'Process Documents'}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="form" className="space-y-4">
            {currentSection && (
              <Card>
                <CardHeader>
                  <CardTitle>{currentSection.section_name}</CardTitle>
                  <CardDescription>{currentSection.description}</CardDescription>
                  <div className="flex items-center space-x-2 mt-2">
                    <Progress value={currentSection.completion_percentage} className="flex-1" />
                    <span className="text-sm font-medium">
                      {currentSection.completion_percentage}%
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {currentSection.fields.map((field) => (
                    <div key={field.field_name} className="space-y-2">
                      <div className="flex items-center">
                        <Label htmlFor={field.field_name}>
                          {field.description}
                          {field.required && <span className="text-red-500 ml-1">*</span>}
                        </Label>
                        {getValueSourceBadge(field.value_source)}
                        {getConfidenceBadge(field.confidence)}
                      </div>
                      <Input
                        id={field.field_name}
                        type={field.field_type === 'NUMBER' ? 'number' : 'text'}
                        value={field.current_value || ''}
                        onChange={(e) => updateField(field.field_name, e.target.value)}
                        placeholder={field.description}
                        className={
                          field.confidence && field.confidence < 0.7
                            ? 'border-yellow-500'
                            : ''
                        }
                      />
                      {field.confidence && field.confidence < 0.7 && (
                        <p className="text-sm text-yellow-600">
                          Low confidence - please verify this value
                        </p>
                      )}
                    </div>
                  ))}

                  {currentSection.missing_required_fields.length > 0 && (
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        Missing required fields: {currentSection.missing_required_fields.join(', ')}
                      </AlertDescription>
                    </Alert>
                  )}

                  <div className="flex space-x-2">
                    <Button onClick={calculateIncome} className="flex-1">
                      Calculate Income
                    </Button>
                    <Button onClick={analyzeGaps} variant="outline" className="flex-1">
                      Analyze Gaps
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="income" className="space-y-4">
            {incomeAnalysis ? (
              <>
                <Card>
                  <CardHeader>
                    <CardTitle>Income Analysis</CardTitle>
                    <CardDescription>
                      Based on Freddie Mac underwriting guidelines
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="p-4 bg-blue-50 rounded-lg">
                      <p className="text-sm text-gray-600 mb-1">Total Monthly Income</p>
                      <p className="text-3xl font-bold text-blue-600">
                        ${incomeAnalysis.total_monthly_income.toLocaleString()}
                      </p>
                    </div>

                    <div className="space-y-2">
                      <h3 className="font-semibold">Income Sources</h3>
                      {incomeAnalysis.income_sources.map((source, idx) => (
                        <div key={idx} className="p-3 bg-white border rounded-lg">
                          <div className="flex justify-between items-start">
                            <div>
                              <p className="font-medium">{source.source_type}</p>
                              {source.employer_name && (
                                <p className="text-sm text-gray-600">{source.employer_name}</p>
                              )}
                            </div>
                            <p className="font-semibold">
                              ${source.amount.toLocaleString()}/{source.frequency}
                            </p>
                          </div>
                          <div className="flex space-x-2 mt-2">
                            {source.is_stable && (
                              <Badge variant="default">Stable</Badge>
                            )}
                            {source.has_continuance && (
                              <Badge variant="default">Continuance</Badge>
                            )}
                          </div>
                          {source.notes && (
                            <p className="text-sm text-gray-600 mt-2">{source.notes}</p>
                          )}
                        </div>
                      ))}
                    </div>

                    {incomeAnalysis.issues.length > 0 && (
                      <Alert>
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>
                          <p className="font-semibold mb-1">Issues:</p>
                          <ul className="list-disc list-inside space-y-1">
                            {incomeAnalysis.issues.map((issue, idx) => (
                              <li key={idx} className="text-sm">{issue}</li>
                            ))}
                          </ul>
                        </AlertDescription>
                      </Alert>
                    )}

                    {incomeAnalysis.recommendations.length > 0 && (
                      <div className="space-y-2">
                        <h3 className="font-semibold">Recommendations</h3>
                        <ul className="list-disc list-inside space-y-1">
                          {incomeAnalysis.recommendations.map((rec, idx) => (
                            <li key={idx} className="text-sm text-gray-700">{rec}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {incomeAnalysis.potential_income_increases.length > 0 && (
                      <div className="space-y-2">
                        <h3 className="font-semibold">Increase Your Qualifying Income</h3>
                        {incomeAnalysis.potential_income_increases.map((increase, idx) => (
                          <div key={idx} className="p-3 bg-green-50 border border-green-200 rounded-lg">
                            <p className="font-medium text-green-900">{increase.suggestion}</p>
                            <p className="text-sm text-green-700 mt-1">{increase.potential_benefit}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card>
                <CardContent className="p-8 text-center">
                  <DollarSign className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                  <p className="text-gray-600 mb-4">
                    Upload documents and process them to calculate income
                  </p>
                  <Button onClick={() => setActiveTab('upload')}>
                    Go to Upload
                  </Button>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="gaps" className="space-y-4">
            {gapAnalysis ? (
              <>
                <Card>
                  <CardHeader>
                    <CardTitle>Gap Analysis</CardTitle>
                    <CardDescription>
                      Missing information and document recommendations
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-3 gap-4">
                      <div className="p-4 bg-red-50 rounded-lg">
                        <p className="text-sm text-gray-600 mb-1">Critical</p>
                        <p className="text-2xl font-bold text-red-600">
                          {gapAnalysis.critical_gaps}
                        </p>
                      </div>
                      <div className="p-4 bg-yellow-50 rounded-lg">
                        <p className="text-sm text-gray-600 mb-1">Warnings</p>
                        <p className="text-2xl font-bold text-yellow-600">
                          {gapAnalysis.warning_gaps}
                        </p>
                      </div>
                      <div className="p-4 bg-blue-50 rounded-lg">
                        <p className="text-sm text-gray-600 mb-1">Completion</p>
                        <p className="text-2xl font-bold text-blue-600">
                          {gapAnalysis.completion_percentage}%
                        </p>
                      </div>
                    </div>

                    {gapAnalysis.suggested_documents.length > 0 && (
                      <div className="space-y-2">
                        <h3 className="font-semibold">Suggested Documents</h3>
                        <ul className="space-y-2">
                          {gapAnalysis.suggested_documents.map((doc, idx) => (
                            <li key={idx} className="flex items-start space-x-2">
                              <FileText className="w-5 h-5 text-blue-500 mt-0.5" />
                              <span className="text-sm">{doc}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <div className="space-y-2">
                      <h3 className="font-semibold">Information Gaps</h3>
                      {gapAnalysis.gaps.slice(0, 10).map((gap, idx) => (
                        <div
                          key={idx}
                          className={`p-3 border rounded-lg ${
                            gap.severity === 'critical'
                              ? 'bg-red-50 border-red-200'
                              : gap.severity === 'warning'
                              ? 'bg-yellow-50 border-yellow-200'
                              : 'bg-blue-50 border-blue-200'
                          }`}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center space-x-2">
                                <Badge
                                  variant={
                                    gap.severity === 'critical'
                                      ? 'destructive'
                                      : gap.severity === 'warning'
                                      ? 'secondary'
                                      : 'default'
                                  }
                                >
                                  {gap.severity}
                                </Badge>
                                <p className="font-medium">{gap.field_name}</p>
                              </div>
                              <p className="text-sm text-gray-700 mt-1">{gap.description}</p>
                              <p className="text-sm text-gray-600 mt-1 italic">
                                {gap.recommendation}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    <Button onClick={() => setActiveTab('upload')} className="w-full">
                      Upload More Documents
                    </Button>
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card>
                <CardContent className="p-8 text-center">
                  <AlertCircle className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                  <p className="text-gray-600 mb-4">
                    Process documents to see gap analysis
                  </p>
                  <Button onClick={() => setActiveTab('upload')}>
                    Go to Upload
                  </Button>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

export default App;
