import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Switch } from '../components/ui/switch';
import { Button } from '../components/ui/button';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { useToast } from '../hooks/use-toast';
import { 
  Settings as SettingsIcon, 
  Brain, 
  Shield, 
  Palette, 
  Trash2, 
  Save,
  Sparkles,
  Globe,
  User,
  Eye,
  EyeOff
} from 'lucide-react';

export default function Settings() {
  const { user, updateUser } = useAuth();
  const { toast } = useToast();
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  // Privacy settings
  const [personalizationEnabled, setPersonalizationEnabled] = useState(true);
  const [globalLearningEnabled, setGlobalLearningEnabled] = useState(false);
  
  // Preferences
  const [preferences, setPreferences] = useState(null);
  const [insights, setInsights] = useState(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      
      // Load preferences
      const prefRes = await api.get('/api/learning/preferences');
      if (prefRes.data.success) {
        setPreferences(prefRes.data.preferences);
        setPersonalizationEnabled(prefRes.data.personalization_enabled);
        setGlobalLearningEnabled(prefRes.data.global_learning_enabled);
      }
      
      // Load insights
      const insightRes = await api.get('/api/learning/insights');
      if (insightRes.data.success) {
        setInsights(insightRes.data.insights);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const savePrivacySettings = async () => {
    try {
      setSaving(true);
      const res = await api.put('/api/learning/privacy', null, {
        params: {
          personalization_enabled: personalizationEnabled,
          global_learning_enabled: globalLearningEnabled
        }
      });
      
      if (res.data.success) {
        toast({
          title: "Settings Saved",
          description: "Your privacy settings have been updated.",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save settings.",
        variant: "destructive"
      });
    } finally {
      setSaving(false);
    }
  };

  const resetPreferences = async () => {
    if (!window.confirm('Are you sure you want to reset all your learning preferences?')) {
      return;
    }
    
    try {
      const res = await api.delete('/api/learning/preferences');
      if (res.data.success) {
        setPreferences(null);
        toast({
          title: "Preferences Reset",
          description: "Your learning preferences have been cleared.",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to reset preferences.",
        variant: "destructive"
      });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <SettingsIcon className="h-8 w-8" />
          Settings
        </h1>
        <p className="text-muted-foreground mt-2">
          Manage your Nirman preferences and privacy settings
        </p>
      </div>

      <Tabs defaultValue="privacy" className="space-y-6">
        <TabsList className="grid grid-cols-3 w-full max-w-md">
          <TabsTrigger value="privacy" className="flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Privacy
          </TabsTrigger>
          <TabsTrigger value="learning" className="flex items-center gap-2">
            <Brain className="h-4 w-4" />
            Learning
          </TabsTrigger>
          <TabsTrigger value="preferences" className="flex items-center gap-2">
            <Palette className="h-4 w-4" />
            Preferences
          </TabsTrigger>
        </TabsList>

        {/* Privacy Tab */}
        <TabsContent value="privacy" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Personalization
              </CardTitle>
              <CardDescription>
                Let Nirman learn from your projects to give you better suggestions
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
                <div className="flex-1">
                  <Label htmlFor="personalization" className="text-base font-medium">
                    Enable Personalization
                  </Label>
                  <p className="text-sm text-muted-foreground mt-1">
                    Nirman will remember your preferred themes, layouts, and sections to make better suggestions in future projects.
                  </p>
                </div>
                <Switch
                  id="personalization"
                  checked={personalizationEnabled}
                  onCheckedChange={setPersonalizationEnabled}
                />
              </div>

              <div className="flex items-start gap-3 p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
                <Eye className="h-5 w-5 text-green-600 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium text-green-700">Your data stays yours</p>
                  <p className="text-green-600/80">
                    Personalization only uses your own project history. No data is shared with others.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="h-5 w-5" />
                Improve Nirman
              </CardTitle>
              <CardDescription>
                Help make Nirman better for everyone (opt-in)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
                <div className="flex-1">
                  <Label htmlFor="global-learning" className="text-base font-medium">
                    Contribute to Global Learning
                  </Label>
                  <p className="text-sm text-muted-foreground mt-1">
                    Share anonymized patterns from your successful projects to help improve suggestions for all users.
                  </p>
                </div>
                <Switch
                  id="global-learning"
                  checked={globalLearningEnabled}
                  onCheckedChange={setGlobalLearningEnabled}
                />
              </div>

              <div className="flex items-start gap-3 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                <Shield className="h-5 w-5 text-blue-600 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium text-blue-700">Privacy Protected</p>
                  <p className="text-blue-600/80">
                    We only use anonymized structural patterns. Your content, API keys, and personal data are never collected.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Button onClick={savePrivacySettings} disabled={saving} className="w-full">
            {saving ? (
              <span className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Saving...
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <Save className="h-4 w-4" />
                Save Privacy Settings
              </span>
            )}
          </Button>
        </TabsContent>

        {/* Learning Insights Tab */}
        <TabsContent value="learning" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                Your Building Insights
              </CardTitle>
              <CardDescription>
                See what Nirman has learned about your preferences
              </CardDescription>
            </CardHeader>
            <CardContent>
              {insights ? (
                <div className="space-y-6">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 bg-muted/50 rounded-lg text-center">
                      <div className="text-2xl font-bold">{insights.total_projects || 0}</div>
                      <div className="text-sm text-muted-foreground">Projects</div>
                    </div>
                    <div className="p-4 bg-muted/50 rounded-lg text-center">
                      <div className="text-2xl font-bold">{insights.total_builds || 0}</div>
                      <div className="text-sm text-muted-foreground">Builds</div>
                    </div>
                    <div className="p-4 bg-muted/50 rounded-lg text-center">
                      <div className="text-2xl font-bold">{insights.success_rate || 0}%</div>
                      <div className="text-sm text-muted-foreground">Success Rate</div>
                    </div>
                    <div className="p-4 bg-muted/50 rounded-lg text-center">
                      <div className="text-2xl font-bold">{insights.avg_iterations || 0}</div>
                      <div className="text-sm text-muted-foreground">Avg Iterations</div>
                    </div>
                  </div>

                  {insights.top_sections?.length > 0 && (
                    <div>
                      <h4 className="font-medium mb-2">Your Favorite Sections</h4>
                      <div className="flex flex-wrap gap-2">
                        {insights.top_sections.map((section, idx) => (
                          <span key={idx} className="px-3 py-1 bg-primary/10 text-primary rounded-full text-sm">
                            {section}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {insights.preferred_industries?.length > 0 && (
                    <div>
                      <h4 className="font-medium mb-2">Industries You Build For</h4>
                      <div className="flex flex-wrap gap-2">
                        {insights.preferred_industries.map((industry, idx) => (
                          <span key={idx} className="px-3 py-1 bg-secondary/50 rounded-full text-sm">
                            {industry}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Brain className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No insights yet. Start building projects to see your patterns!</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Preferences Tab */}
        <TabsContent value="preferences" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Palette className="h-5 w-5" />
                Learned Preferences
              </CardTitle>
              <CardDescription>
                These preferences are automatically learned from your projects
              </CardDescription>
            </CardHeader>
            <CardContent>
              {preferences ? (
                <div className="space-y-6">
                  {preferences.preferred_theme && (
                    <div>
                      <h4 className="font-medium mb-3">Theme</h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        {preferences.preferred_theme.primary_color && (
                          <div className="flex items-center gap-2">
                            <div 
                              className="w-6 h-6 rounded-full border"
                              style={{ backgroundColor: preferences.preferred_theme.primary_color }}
                            />
                            <span className="text-sm">Primary</span>
                          </div>
                        )}
                        {preferences.preferred_theme.font_family && (
                          <div className="text-sm">
                            Font: <span className="font-medium">{preferences.preferred_theme.font_family}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  <div>
                    <h4 className="font-medium mb-2">Style</h4>
                    <p className="text-sm text-muted-foreground">
                      Tone: <span className="font-medium">{preferences.preferred_tone || 'Modern'}</span>
                    </p>
                  </div>

                  {preferences.preferred_sections?.length > 0 && (
                    <div>
                      <h4 className="font-medium mb-2">Frequently Used Sections</h4>
                      <div className="flex flex-wrap gap-2">
                        {preferences.preferred_sections.map((section, idx) => (
                          <span key={idx} className="px-3 py-1 bg-muted rounded-full text-sm">
                            {section}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Palette className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No preferences learned yet. Build more projects!</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="border-destructive/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-destructive">
                <Trash2 className="h-5 w-5" />
                Reset Learning Data
              </CardTitle>
              <CardDescription>
                Clear all learned preferences and start fresh
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button 
                variant="destructive" 
                onClick={resetPreferences}
                className="w-full"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Reset All Preferences
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
