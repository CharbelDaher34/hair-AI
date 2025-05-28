
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { CheckCircle, XCircle, Eye, Star, Filter } from "lucide-react";
import { useParams, Link } from "react-router-dom";

const MatchedCandidates = () => {
  const { id } = useParams();
  const [scoreThreshold, setScoreThreshold] = useState([70]);
  const [constraintFilter, setConstraintFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  // Mock job data
  const job = {
    id: 1,
    title: "Senior Frontend Developer",
    totalCandidates: 45,
  };

  const candidates = [
    {
      id: 1,
      name: "Alice Johnson",
      email: "alice.johnson@email.com",
      score: 92,
      satisfiedConstraints: 8,
      totalConstraints: 10,
      status: "pending",
      skillMatch: ["React", "TypeScript", "Node.js"],
      missingSkills: ["AWS", "GraphQL"],
      experience: "6 years",
      lastActivity: "2024-01-20",
    },
    {
      id: 2,
      name: "Bob Smith",
      email: "bob.smith@email.com", 
      score: 88,
      satisfiedConstraints: 7,
      totalConstraints: 10,
      status: "accepted",
      skillMatch: ["React", "JavaScript", "CSS"],
      missingSkills: ["TypeScript", "Testing", "CI/CD"],
      experience: "4 years",
      lastActivity: "2024-01-19",
    },
    {
      id: 3,
      name: "Carol Williams",
      email: "carol.williams@email.com",
      score: 85,
      satisfiedConstraints: 9,
      totalConstraints: 10,
      status: "pending",
      skillMatch: ["React", "TypeScript", "Redux", "Testing"],
      missingSkills: ["Node.js"],
      experience: "5 years",
      lastActivity: "2024-01-18",
    },
    {
      id: 4,
      name: "David Brown",
      email: "david.brown@email.com",
      score: 82,
      satisfiedConstraints: 6,
      totalConstraints: 10,
      status: "rejected",
      skillMatch: ["JavaScript", "HTML", "CSS"],
      missingSkills: ["React", "TypeScript", "Modern Framework", "State Management"],
      experience: "3 years",
      lastActivity: "2024-01-17",
    },
    {
      id: 5,
      name: "Emma Davis",
      email: "emma.davis@email.com",
      score: 79,
      satisfiedConstraints: 7,
      totalConstraints: 10,
      status: "pending",
      skillMatch: ["React", "JavaScript", "Redux"],
      missingSkills: ["TypeScript", "Testing", "Advanced React"],
      experience: "4 years",
      lastActivity: "2024-01-16",
    },
    {
      id: 6,
      name: "Frank Wilson",
      email: "frank.wilson@email.com",
      score: 76,
      satisfiedConstraints: 5,
      totalConstraints: 10,
      status: "pending",
      skillMatch: ["HTML", "CSS", "JavaScript"],
      missingSkills: ["React", "TypeScript", "Modern Framework", "State Management", "Testing"],
      experience: "2 years",
      lastActivity: "2024-01-15",
    },
  ];

  const filteredCandidates = candidates.filter(candidate => {
    const meetsScore = candidate.score >= scoreThreshold[0];
    const meetsConstraints = constraintFilter === "all" || 
                           (constraintFilter === "high" && candidate.satisfiedConstraints >= 8) ||
                           (constraintFilter === "medium" && candidate.satisfiedConstraints >= 5 && candidate.satisfiedConstraints < 8) ||
                           (constraintFilter === "low" && candidate.satisfiedConstraints < 5);
    const meetsStatus = statusFilter === "all" || candidate.status === statusFilter;
    
    return meetsScore && meetsConstraints && meetsStatus;
  });

  const getStatusVariant = (status: string): "default" | "secondary" | "destructive" => {
    switch (status) {
      case "accepted":
        return "default";
      case "rejected":
        return "destructive";
      default:
        return "secondary";
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return "text-green-600";
    if (score >= 80) return "text-blue-600";
    if (score >= 70) return "text-orange-600";
    return "text-red-600";
  };

  const handleAccept = (candidateId: number) => {
    console.log("Accepting candidate:", candidateId);
  };

  const handleReject = (candidateId: number) => {
    console.log("Rejecting candidate:", candidateId);
  };

  return (
    <div className="flex-1 space-y-8 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Matched Candidates</h1>
          <p className="text-muted-foreground">
            {job.title} • {filteredCandidates.length} of {candidates.length} candidates shown
          </p>
        </div>
        <Button variant="outline" asChild>
          <Link to={`/jobs/${id}`}>
            <Eye className="mr-2 h-4 w-4" />
            Back to Job
          </Link>
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Filter className="h-5 w-5" />
              Filters
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-3">
              <Label>Score Threshold: {scoreThreshold[0]}%</Label>
              <Slider
                value={scoreThreshold}
                onValueChange={setScoreThreshold}
                max={100}
                min={0}
                step={5}
                className="w-full"
              />
            </div>

            <div className="space-y-2">
              <Label>Constraint Match</Label>
              <Select value={constraintFilter} onValueChange={setConstraintFilter}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Candidates</SelectItem>
                  <SelectItem value="high">High Match (8+ constraints)</SelectItem>
                  <SelectItem value="medium">Medium Match (5-7 constraints)</SelectItem>
                  <SelectItem value="low">Low Match (&lt;5 constraints)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Status</Label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="accepted">Accepted</SelectItem>
                  <SelectItem value="rejected">Rejected</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="pt-4 border-t">
              <div className="text-sm text-muted-foreground space-y-1">
                <div>Total: {candidates.length} candidates</div>
                <div>Filtered: {filteredCandidates.length} candidates</div>
                <div>Avg Score: {Math.round(candidates.reduce((sum, c) => sum + c.score, 0) / candidates.length)}%</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="lg:col-span-3">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Star className="h-5 w-5" />
                Candidate Matches
              </CardTitle>
              <CardDescription>
                Candidates ranked by compatibility with job requirements
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Candidate</TableHead>
                    <TableHead>Score</TableHead>
                    <TableHead>Constraints</TableHead>
                    <TableHead>Skills Match</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredCandidates.map((candidate) => (
                    <TableRow key={candidate.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{candidate.name}</div>
                          <div className="text-sm text-muted-foreground">{candidate.email}</div>
                          <div className="text-xs text-muted-foreground">
                            {candidate.experience} experience
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <span className={`font-bold text-lg ${getScoreColor(candidate.score)}`}>
                            {candidate.score}%
                          </span>
                          <div className="w-16 h-2 bg-muted rounded-full">
                            <div
                              className="h-full bg-primary rounded-full"
                              style={{ width: `${candidate.score}%` }}
                            />
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-center">
                          <div className="font-medium">
                            {candidate.satisfiedConstraints}/{candidate.totalConstraints}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {Math.round((candidate.satisfiedConstraints / candidate.totalConstraints) * 100)}%
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1 max-w-[200px]">
                          <div className="flex flex-wrap gap-1">
                            {candidate.skillMatch.slice(0, 3).map((skill, index) => (
                              <Badge key={index} variant="default" className="text-xs">
                                {skill}
                              </Badge>
                            ))}
                            {candidate.skillMatch.length > 3 && (
                              <Badge variant="outline" className="text-xs">
                                +{candidate.skillMatch.length - 3}
                              </Badge>
                            )}
                          </div>
                          {candidate.missingSkills.length > 0 && (
                            <div className="text-xs text-muted-foreground">
                              Missing: {candidate.missingSkills.slice(0, 2).join(", ")}
                              {candidate.missingSkills.length > 2 && "..."}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusVariant(candidate.status)}>
                          {candidate.status.charAt(0).toUpperCase() + candidate.status.slice(1)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex space-x-1">
                          {candidate.status === "pending" && (
                            <>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleAccept(candidate.id)}
                              >
                                <CheckCircle className="h-3 w-3" />
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleReject(candidate.id)}
                              >
                                <XCircle className="h-3 w-3" />
                              </Button>
                            </>
                          )}
                          <Button size="sm" variant="outline" asChild>
                            <Link to={`/applications/${candidate.id}`}>
                              <Eye className="h-3 w-3" />
                            </Link>
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default MatchedCandidates;
