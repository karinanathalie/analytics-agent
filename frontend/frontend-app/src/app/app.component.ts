import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { CommonModule} from '@angular/common';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [ FormsModule, CommonModule],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
})
export class AppComponent {
  title = 'Analytics Agent';
  userQuery = '';
  result : any = null;
  loading = false;
  error = '';

  constructor(private http: HttpClient) {}

  ask() {
    if (!this.userQuery) {
      this.error = 'Please enter your question.';
      return;
    }
    this.loading = true;
    this.error = '';
    this.result = null;

    this.http.post<any>('http://127.0.0.1:8000/ask', { user_query: this.userQuery }).subscribe({
      next: (data) => {
        this.result = data.result;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Error contacting backend: ' + (err?.message || err);
        this.loading = false;
      }
    });
  }
}
